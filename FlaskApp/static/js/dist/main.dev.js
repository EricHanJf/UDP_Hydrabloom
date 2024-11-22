"use strict";

var aliveSecond = 0;
var hearBeatRate = 5000;
var pubnub;
var appChannel = "xhanhan_pi_channel";

function time() {
  var d = new Date();
  var currentSecond = d.getTime();

  if (currentSecond - aliveSecond > hearBeatRate + 1000) {
    document.getElementById("connection_id").innerHTML = "Dead";
  } else {
    document.getElementById("connection_id").innerHTML = "Alive";
  }

  setTimeout('time()', 1000);
}

function keepAlive() {
  fetch('/keep_alive').then(function (response) {
    if (response.ok) {
      var date = new Date();
      aliveSecond = date.getTime();
      return response.json();
    }

    throw new Error("Server offline");
  }) // .then(responseJson => {
  //     if (responseJson.motion == 1) {
  //         document.getElementById("motion_id").innerHTML = "Motion";
  //     } else {
  //         document.getElementById("motion_id").innerHTML = "No Motion";
  //     }
  // })
  ["catch"](function (error) {
    return console.log(error);
  });
  setTimeout('keepAlive()', hearBeatRate);
}

function handleClick(cb) {
  if (cb.checked) {
    value = "on";
  } else {
    value = "off";
  } // sendEvent(cb.id + "-" + value);


  publicMessage({
    "buzzer": value
  });
} // function sendEvent(value) {
//     fetch('/status=' + value, {
//         method: "POST"
//     })
// }


var setupPubNUb = function setupPubNUb() {
  pubnub = new pubnub({
    publishkey: 'pub-c-18b517bb-ecb2-4940-badd-117a53aec456',
    subscribekey: 'sub-c-7cb4f455-1d58-4487-81d5-460d437b7daf',
    userId: "Xhanhan_Web_App"
  }); //creat a channel

  var channer = pubnub.channel(appChannel); //create a subscription

  var subscription = channel.subscription();
  pubnub.addListener({
    status: function status(s) {
      console.log('Status', s.category);
    }
  });

  subscription.onMessage = function (messageEvent) {
    handleMessage(messageEvent.message);
  };

  subscription.subscribe();
};

var publishMessage = function publishMessage(message) {
  var publishPayload;
  return regeneratorRuntime.async(function publishMessage$(_context) {
    while (1) {
      switch (_context.prev = _context.next) {
        case 0:
          publishPayload = {
            channel: appChannel,
            message: message
          };
          _context.next = 3;
          return regeneratorRuntime.awrap(pubnub.publish(publishPayload));

        case 3:
        case "end":
          return _context.stop();
      }
    }
  });
};

function handleMessage(message) {
  if (message == '"Motion":"Yes"') {
    document.getElementById("motion_id").innerHTML = "Yes";
  }

  if (message == '"Motion":"No"') {
    document.getElementById("motion_id").innerHTML = "No";
  }
}