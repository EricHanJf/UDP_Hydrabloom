"use strict";

// // let aliveSecond = 0;
// // let hearBeatRate = 5000;
// let pubnub;
// let app_Channel = "Hydrabloom"
// // function time() {
// //     let d = new Date();
// //     let currentSecond = d.getTime();
// //     if (currentSecond - aliveSecond > hearBeatRate + 1000) {
// //         document.getElementById("connection_id").innerHTML = "Dead";
// //     } else {
// //         document.getElementById("connection_id").innerHTML = "Alive";
// //     }
// //     setTimeout('time()', 1000);
// // }
// // function keepAlive() {
// //     fetch('/keep_alive')
// //         .then(response => {
// //             if (response.ok) {
// //                 let date = new Date();
// //                 aliveSecond = date.getTime();
// //                 return response.json();
// //             }
// //             throw new Error("Server offline");
// //         })
// //         // .then(responseJson => {
// //         //     if (responseJson.motion == 1) {
// //         //         document.getElementById("motion_id").innerHTML = "Motion";
// //         //     } else {
// //         //         document.getElementById("motion_id").innerHTML = "No Motion";
// //         //     }
// //         // })
// //         .catch(error => console.log(error));
// //     setTimeout('keepAlive()', hearBeatRate);
// // }
// function handleClick(cb) {
//     if (cb.checked) {
//         value = "on";
//     } else {
//         value = "off";
//     }
//     // sendEvent(cb.id + "-" + value);
//     publicMessage({ "buzzer": value })
// }
// const setupPubNUb = () => {
//     pubnub = new pubnub({
//         publishkey: 'pub-c-75d6d309-722b-419e-b589-e4f425b00fcb',
//         subscribekey: 'sub-c-ccf0e37c-5f9b-4d4e-8455-af8f49720443',
//         userId: "Hydrabloom",
//     })
//     //creat a channel
//     const channer = pubnub.channel(app_Channel);
//     //create a subscription
//     const subscription = channel.subscription();
//     pubnub.addListener({
//         status: (s) => {
//             console.log('Status', s.category);
//         },
//     })
//     subscription.onMessage = (messageEvent) => {
//         handleMessage(messageEvent.message);
//     }
//     subscription.subscribe();
// };
// const publishMessage = async (message) => {
//     const publishPayload = {
//         channel: appChannel,
//         message: message,
//     };
//     await pubnub.publish(publishPayload)
// }
// function handleMessage(message) {
//     if (message == '"Motion":"Yes"') {
//         document.getElementById("motion_id").innerHTML = "Yes";
//     }
//     if (message == '"Motion":"No"') {
//         document.getElementById("motion_id").innerHTML = "No";
//     }
// }
document.addEventListener("DOMContentLoaded", function () {
  var ledOnButton = document.getElementById("ledOnButton");
  var ledOffButton = document.getElementById("ledOffButton");
  var statusElement = document.getElementById("status"); // Setup PubNub

  var pubnub;

  var setupPubNub = function setupPubNub() {
    // Initialize PubNub
    var pubnubConfig = {
      publishKey: 'pub-c-75d6d309-722b-419e-b589-e4f425b00fcb',
      subscribeKey: 'sub-c-ccf0e37c-5f9b-4d4e-8455-af8f49720443',
      uuid: 'Hydrabloom' // Unique identifier for the client

    };
    pubnub = new PubNub(pubnubConfig); // Subscribe to the channel to listen for incoming messages

    pubnub.subscribe({
      channels: ['Hydrabloom'],
      withPresence: true
    }); // Set up listener for incoming messages

    pubnub.addListener({
      message: handleMessage,
      status: function status(statusEvent) {
        console.log("PubNub status:", statusEvent);
      }
    });
  }; // Handle the click event to publish messages to the PubNub channel


  var handleClick = function handleClick(action) {
    var message = {
      command: action === "on" ? "LED_ON" : "LED_OFF"
    };
    publishMessage(message);
  }; // Publish message to the PubNub channel


  var publishMessage = function publishMessage(message) {
    pubnub.publish({
      channel: 'Hydrabloom',
      // Replace with your channel
      message: message,
      callback: function callback(response) {
        console.log("Message sent:", response); // Optionally, update the UI based on the response

        updateStatus("LED is ".concat(message.led.toUpperCase()));
      },
      error: function error(_error) {
        console.error("Error publishing message:", _error);
      }
    });
  }; // Handle messages received from PubNub


  var handleMessage = function handleMessage(message) {
    console.log("Received message:", message);
    var command = message.message.command; // Update the status UI based on the action (ON/OFF)

    if (command === 'LED_ON') {
      updateStatus("LED is ON");
    } else if (command === 'LED_OFF') {
      updateStatus("LED is OFF");
    } else {
      console.log("Unknown command:", command);
    }
  }; // Update the UI with the current LED status


  var updateStatus = function updateStatus(status) {
    statusElement.textContent = "Status: ".concat(status);
  }; // Initialize PubNub when the page is loaded


  setupPubNub(); // Event listener for the "Turn ON LED" button

  ledOnButton.addEventListener("click", function () {
    handleClick("on");
  }); // Event listener for the "Turn OFF LED" button

  ledOffButton.addEventListener("click", function () {
    handleClick("off");
  });
});