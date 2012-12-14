if (!phantom.injectJs('async.min.js')) {
  exit('Failed to load async library.');
}

var env = require('system').env;
var fs = require('fs');
var page = require('webpage').create();

// var LOGIN_URL = 'file:///c:/temp/mock.html';
var LOGIN_URL = 'http://puzzles.telegraph.co.uk/site/index.php';

function debug(msg) {
  console.log('DEBUG: ' + msg);
}

function exit(msg) {
  if (msg) {
    console.log(msg);
    phantom.exit(1);
  } else {
    phantom.exit(0);
  }
}

function loadConfig() {
  try {
    var baseDir = env['HOME'] || '.';
    var configFile = baseDir + '/.telegraphrc';
    var is = fs.open(configFile, 'r');
    var config = eval(is.read());
    is.close();
    return config;
  } catch (e) {
    throw new Error('Failed to load config: ' + e);
  }
}

function setEventHandlers() {
  page.settings.userAgent = 'Mozilla/5.0 (Windows NT 5.1; rv:9.0) Gecko/20100101 Firefox/9.0';
  page.onAlert = function(msg) {
    console.log('ALERT: ' + msg);
  };

  page.onConsoleMessage = function(msg, lineNum, sourceId) {
    console.log('CONSOLE: ' + msg + ' (from line #' + lineNum + ' in "' + sourceId + '")');
  };

  page.onError = function(msg, trace) {
    var msgStack = ['ERROR: ' + msg];
    if (trace) {
      msgStack.push('TRACE:');
      trace.forEach(function(t) {
        msgStack.push(' -> ' + t.file + ': ' + t.line + (t.function ? ' (in function "' + t.function + '")' : ''));
      });
    }
    console.error(msgStack.join('\n'));
    page.render('error.png');
  };

  page.onNavigationRequested = function(url, type, willNavigate, main) {
    console.log('Trying to navigate to: ' + url);
    console.log('Caused by: ' + type);
    console.log('Will actually navigate: ' + willNavigate);
    console.log('Sent from the page\'s main frame: ' + main);
  }

  page.onLoadFinished = function(status) {
    debug('loadFinished(' + status + ')');
  }

}

function waitFor(testFx, onReady, timeOutMillis) {
  var maxtimeOutMillis = timeOutMillis ? timeOutMillis : 3000, //< Default Max Timout is 3s
      start = new Date().getTime(),
      condition = false,
      interval = setInterval(function() {
        if ( (new Date().getTime() - start < maxtimeOutMillis) && !condition ) {
          // If not time-out yet and condition not yet fulfilled
          condition = (typeof(testFx) === "string" ? eval(testFx) : testFx()); //< defensive code
        } else {
          if(!condition) {
            // If condition still not fulfilled (timeout but condition is 'false')
            console.log("'waitFor()' timeout");
            phantom.exit(1);
          } else {
            // Condition fulfilled (timeout and/or condition is 'true')
            console.log("'waitFor()' finished in " + (new Date().getTime() - start) + "ms.");
            typeof(onReady) === "string" ? eval(onReady) : onReady(); //< Do what it's supposed to do once the condition is fulfilled
            clearInterval(interval); //< Stop this interval
          }
        }
      }, 250); //< repeat check every 250ms
}


function openLoginForm(next) {
  debug('openLoginForm');
  page.open(LOGIN_URL, function(status) {
    if (status !== 'success') {
      next('Failed to open url \'' + LOGIN_URL + '\'.');
    } else {
      next(null);
    }
  });
}  

function submitLoginForm(next) {
  debug('submitLoginForm()');
  page.evaluate(function(username, password) {
    var email = document.getElementById('email');
    var password = document.getElementById('password');
    email.value = username;
    password.value = password;
    document.login.submit();
  }, config['username'], config['password']);
  next(null);
}

function waitForLogin(next) {
  debug('waitForLogin');
  waitFor(
    function() {
      return page.evaluate(function() {
        if (document.getElementById('welcome_message')) {
          return 'success';
        } else if (document.getElementById('popup-login-err')) {
          return 'failed';
        } else {
          return false;
        }
      });
    },
    function(result) {
      console.log('Login result is: \'' + result + '\'.')
      if (result == 'success') {
        next(null);
      } else {
        var os = fs.open('error.html', 'w');
        os.write(page.content);
        os.close();
        next('Login failed');
      }
    },
    30000);
}

//
// Main program.
//
setInterval(function() {exit('Timeout')}, 30000);
var config = loadConfig();
setEventHandlers();
try {
  async.waterfall([
    openLoginForm,
    submitLoginForm,
    waitForLogin
    ], exit);
} catch (e) {
  console.log(e);
  phantom.exit(0);
}
console.log('Starting...');
