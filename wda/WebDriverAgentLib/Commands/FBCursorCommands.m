/**
 * Red dot cursor overlay — visible system-wide via WDA's test runner process.
 * Creates a UIWindow at windowLevel above alerts that shows a red dot.
 */

#import "FBCursorCommands.h"

#import "FBRouteRequest.h"
#import "FBSession.h"

static UIWindow *_cursorWindow = nil;
static UIView *_dotView = nil;

@implementation FBCursorCommands

#pragma mark - <FBCommandHandler>

+ (NSArray *)routes
{
  return
  @[
    [[FBRoute POST:@"/wda/cursor/show"].withoutSession respondWithTarget:self action:@selector(handleShow:)],
    [[FBRoute POST:@"/wda/cursor/hide"].withoutSession respondWithTarget:self action:@selector(handleHide:)],
    [[FBRoute POST:@"/wda/cursor/move"].withoutSession respondWithTarget:self action:@selector(handleMove:)],
    [[FBRoute GET:@"/wda/cursor"].withoutSession respondWithTarget:self action:@selector(handleStatus:)],
  ];
}

+ (void)ensureWindow
{
  if (_cursorWindow) return;

  dispatch_block_t setup = ^{
    CGRect screen = UIScreen.mainScreen.bounds;

    _cursorWindow = [[UIWindow alloc] initWithFrame:screen];
    _cursorWindow.windowLevel = UIWindowLevelAlert + 2000;
    _cursorWindow.backgroundColor = [UIColor clearColor];
    _cursorWindow.userInteractionEnabled = NO;
    _cursorWindow.opaque = NO;

    UIViewController *vc = [[UIViewController alloc] init];
    vc.view.backgroundColor = [UIColor clearColor];
    vc.view.userInteractionEnabled = NO;
    _cursorWindow.rootViewController = vc;

    CGFloat sz = 24.0;
    _dotView = [[UIView alloc] initWithFrame:CGRectMake(0, 0, sz, sz)];
    _dotView.backgroundColor = [UIColor systemRedColor];
    _dotView.layer.cornerRadius = sz / 2.0;
    _dotView.layer.borderWidth = 2.5;
    _dotView.layer.borderColor = [UIColor whiteColor].CGColor;
    _dotView.layer.shadowColor = [UIColor blackColor].CGColor;
    _dotView.layer.shadowOffset = CGSizeMake(0, 1);
    _dotView.layer.shadowOpacity = 0.5;
    _dotView.layer.shadowRadius = 3;
    _dotView.center = CGPointMake(screen.size.width / 2, screen.size.height / 2);
    [vc.view addSubview:_dotView];
  };

  if ([NSThread isMainThread]) {
    setup();
  } else {
    dispatch_sync(dispatch_get_main_queue(), setup);
  }
}

#pragma mark - Handlers

+ (id<FBResponsePayload>)handleShow:(FBRouteRequest *)request
{
  [self ensureWindow];
  dispatch_async(dispatch_get_main_queue(), ^{
    _cursorWindow.hidden = NO;
    [_cursorWindow makeKeyAndVisible];
  });
  return FBResponseWithOK();
}

+ (id<FBResponsePayload>)handleHide:(FBRouteRequest *)request
{
  if (_cursorWindow) {
    dispatch_async(dispatch_get_main_queue(), ^{
      _cursorWindow.hidden = YES;
    });
  }
  return FBResponseWithOK();
}

+ (id<FBResponsePayload>)handleMove:(FBRouteRequest *)request
{
  CGFloat x = [request.arguments[@"x"] doubleValue];
  CGFloat y = [request.arguments[@"y"] doubleValue];

  [self ensureWindow];
  dispatch_async(dispatch_get_main_queue(), ^{
    _cursorWindow.hidden = NO;
    _dotView.center = CGPointMake(x, y);
  });
  return FBResponseWithOK();
}

+ (id<FBResponsePayload>)handleStatus:(FBRouteRequest *)request
{
  BOOL visible = (_cursorWindow && !_cursorWindow.hidden);
  CGPoint pos = _dotView ? _dotView.center : CGPointZero;
  return FBResponseWithObject(@{
    @"visible": @(visible),
    @"x": @(pos.x),
    @"y": @(pos.y),
  });
}

@end
