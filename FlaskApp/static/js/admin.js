let pubnub;
let appChannel = "pi-hardware-channel";
let ttl = 5;

user_Id = "{{ user_id }}";
// sendEvent("get_user_token");

const setupPubNub = () => {
  pubnub = new PubNub({
    publishKey: "pub-c-75d6d309-722b-419e-b589-e4f425b00fcb",
    subscribeKey: "sub-c-ccf0e37c-5f9b-4d4e-8455-af8f49720443",
    cryptoModule: PubNub.CryptoModule.aesCbcCryptoModule({
      cipherKey: "secret-123",
    }),
    userId: user_Id,
  });

  // Subscribe to the channel directly using PubNub's subscribe method
  pubnub.subscribe({
    channels: [appChannel],
  });

  // Add listener for events
  pubnub.addListener({
    status: (statusEvent) => {
      console.log("Status Event:", statusEvent.category);
      if (statusEvent.category === "PNConnectedCategory") {
        console.log("Successfully connected to channel:", appChannel);
      } else if (statusEvent.category === "PNDisconnectedCategory") {
        console.log("Disconnected from channel:", appChannel);
      } else if (statusEvent.category === "PNReconnectedCategory") {
        console.log("Reconnected to channel:", appChannel);
      }
    },

    message: (messageEvent) => {
      console.log("Message received:", messageEvent.message);
      // Here you can handle the incoming message
    },
  });

  // Publish a test message
  // pubnub.publish(
  //   {
  //     channel: appChannel,
  //     message: { text: "Test message from PubNub!" },
  //   },
  //   (status, response) => {
  //     if (status.error) {
  //       console.log("Publish failed:", status);
  //     } else {
  //       console.log("Test message published:", response);
  //     }
  //   }
  // );
};

// Function to refresh the token
function refresh_token() {
  sendEvent("get_user_token");
  let refresh_time = (ttl - 1) * 60 * 1000;
  console.log(refresh_time);
  setTimeout("refresh_token()", refresh_time);
}

function grantAccess(ab) {
  let userId = ab.id.split("-")[2];
  let readState = document.getElementById("read-user-" + userId).checked;
  let writeState = document.getElementById("write-user-" + userId).checked;
  console.log("grant-" + userId + "-" + readState + "-" + writeState);
  sendEvent("grant-" + userId + "-" + readState + "-" + writeState);
}

function sendEvent(value) {
  // const baseURL = "https://www.hydrabloom.online/"; // Adjust this to your actual API base URL
  // fetch(baseURL + value, {
  //   method: "POST",
  // })
  fetch(value, {
    method: "POST",
  })
    .then((response) => response.json())
    .then((responseJson) => {
      console.log(responseJson);
      if (responseJson.hasOwnProperty("token")) {
        pbToken = responseJson.token;
        pubnub.setToken(pbToken);
        console.log("Cipher Key: " + responseJson.cipher_key);
        //pubnub.setCipherKey(responseJson.cipher_key);
        pubnub.setUUID(responseJson.uuid);
        subscribe();
      }
    });
}

// Function to subscribe with a token
function subscribe() {
  console.log("Trying to subscribe with token");
  const channel = pubnub.channel(appChannel);
  channel.subscription().subscribe();
}
