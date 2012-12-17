'use strict';
function log(msg) {
  console.log(msg);
}

function debug(msg) {
  log('DEBUG: ' + msg);
}

function exit(msg) {
  if (msg) {
    log(msg);
    phantom.exit(1);
  } else {
    phantom.exit(0);
  }
}

if (!phantom.injectJs('async.min.js')) {
  exit('Failed to load async library.');
}

// var LOGIN_URL = 'file:///c:/temp/mock.html';
var LOGIN_URL = 'http://puzzles.telegraph.co.uk/site/index.php';

function loadConfig() {
  try {
    var env = require('system').env,
      fs = require('fs'),
      baseDir = env.HOME || '.',
      configFile = baseDir + '/.telegraphrc',
      is = fs.open(configFile, 'r'),
      config = eval(is.read());
    is.close();
    return config;
  } catch (e) {
    throw new Error('Failed to load config: ' + e);
  }
}

var page = require('webpage').create(),
  config = loadConfig();

function setEventHandlers() {
  page.settings.userAgent = 'Mozilla/5.0 (Windows NT 5.1; rv:9.0) Gecko/20100101 Firefox/9.0';
  page.onAlert = function (msg) {
    log('ALERT: ' + msg);
  };

  page.onConsoleMessage = function (msg, lineNum, sourceId) {
    log('CONSOLE: ' + msg + ' (from line #' + lineNum + ' in "' + sourceId + '")');
  };

  page.onError = function (msg, trace) {
    var msgStack = ['ERROR: ' + msg];
    if (trace) {
      msgStack.push('TRACE:');
      trace.forEach(function (t) {
        msgStack.push(' -> ' + t.file + ': ' + t.line + (t.function ? ' (in function "' + t.function + '")' : ''));
      });
    }
    console.error(msgStack.join('\n'));
    page.render('error.png');
  };

  page.onNavigationRequested = function (url, type, willNavigate, main) {
    log('Trying to navigate to: ' + url);
    log('Caused by: ' + type);
    log('Will actually navigate: ' + willNavigate);
    log('Sent from the page\'s main frame: ' + main);
  };

  page.onLoadFinished = function (status) {
    debug('loadFinished(' + status + ')');
  };

}

function waitFor(testFx, onReady, timeOutMillis) {
  var maxtimeOutMillis = timeOutMillis || 3000, //< Default Max Timout is 3s
    start = new Date().getTime(),
    condition = false,
    interval = setInterval(function () {
      if ((new Date().getTime() - start < maxtimeOutMillis) && !condition) {
        // If not time-out yet and condition not yet fulfilled
        condition = typeof testFx === "string" ? eval(testFx) : testFx(); //< defensive code
      } else {
        if (!condition) {
          // If condition still not fulfilled (timeout but condition is 'false')
          log("'waitFor()' timeout");
          phantom.exit(1);
        } else {
          // Condition fulfilled (timeout and/or condition is 'true')
          log("'waitFor()' finished in " + (new Date().getTime() - start) + "ms.");
          // Do what it's supposed to do once the condition is fulfilled
          if (typeof onReady === "string") {
            eval(onReady);
          } else {
            onReady();
          }
          clearInterval(interval); //< Stop this interval
        }
      }
    }, 250); //< repeat check every 250ms
}

function saveError() {
  var fs = require('fs'),
    os = fs.open('error.html', 'w');
  os.write(page.content);
  os.close();
  page.render('error.png');
}

function openLoginForm(next) {
  debug('openLoginForm');
  page.open(LOGIN_URL, function (status) {
    if (status !== 'success') {
      next('Failed to open url \'' + LOGIN_URL + '\'.');
    } else {
      next(null);
    }
  });
}

function submitLoginForm(next) {
  debug('submitLoginForm()');
  if (!page.evaluate(function (config_username, config_password) {
    var email = document.getElementById('email'),
      password = document.getElementById('password');
    if (!email) {
      console.log('Email element not found.');
      return false;
    }
    if (!password) {
      console.log('Password element not found.');
      return false;
    }
    email.value = config_username;
    password.value = config_password;
    document.login.submit();
    return true;
  }, config.username, config.password)) {
    saveError();
    next('submitLoginForm() failed.');
  } else {
    next(null);
  }
}

function waitForLogin(next) {
  var waiting = true,
    intervalId = setInterval(function () {
    clearInterval(intervalId);
    waiting = false;
  }, 5000
  );
  debug('waitForLogin');
  waitFor(
    function () {
      return !waiting && page.evaluate(function () {
        var result = false;
        if (document.getElementById('welcome_message')) {
          result = 'success';
        } else if (document.getElementById('popup-login-err')) {
          result = 'failed';
        } else {
          result = false;
        }
        return result;
      });
    },
    function (result) {
      log('Login result is: \'' + result + '\'.');
      if (result === 'success') {
        next(null);
      } else {
        saveError();
        next('Login failed');
      }
    },
    30000
  );
}

//
// Main program.
//
setInterval(function () {
  exit('Timeout');
}, 30000);

setEventHandlers();
try {
  async.waterfall([
    openLoginForm,
    submitLoginForm,
    waitForLogin
  ], exit);
} catch (e) {
  log(e);
  phantom.exit(0);
}
log('Starting...');
