document.addEventListener("DOMContentLoaded", function () {
    const ledOnButton = document.getElementById("ledOnButton");
    const ledOffButton = document.getElementById("ledOffButton");
    const pumpOnButton = document.getElementById("pumpOnButton");
    const pumpOffButton = document.getElementById("pumpOffButton");
    const statusElement = document.getElementById("status"); // LED status element
    const pumpStatusElement = document.getElementById("pumpStatus"); // Pump status element
    const pumpDurationInput = document.getElementById("pumpDurationInput");
  
    let pubnub;
    const channelName = "pi-hardware-channel";
  
    // Unified PubNub setup function
    const setupPubNub = () => {
      pubnub = new PubNub({
        publishKey: "pub-c-5e5be15e-f582-40f2-8c1a-ca9360199f9d",
        subscribeKey: "sub-c-a2447194-c69b-4dbe-a5e8-a4ed24799246",
        authKey:
          "p0F2AkF0GmdeIWBDdHRsGQ4QQ3Jlc6VEY2hhbqFzcGktaGFyZHdhcmUtY2hhbm5lbBjPQ2dycKBDc3BjoEN1c3KgRHV1aWShbnJhc3BiZXJyeXBpNDAwGM9DcGF0pURjaGFuoENncnCgQ3NwY6BDdXNyoER1dWlkoERtZXRhoENzaWdYIPITFuBlkwRBb8BHaX4MAsO_hEak9hV4t2R_c69zO6E_", // Add your auth key here
        cryptoModule: PubNub.CryptoModule.aesCbcCryptoModule({
          cipherKey: "secret-123",
        }),
        uuid: "Hydrabloom",
      });
  
      // Subscribe to the channel
      pubnub.subscribe({
        channels: [channelName],
      });
  
      // Set up listeners
      pubnub.addListener({
        message: handlePubNubMessage,
        status: (statusEvent) => {
          console.log("PubNub status:", statusEvent);
        },
      });
    };
  
    // General message handler
    const handlePubNubMessage = (event) => {
      const channel = event.channel;
      const message = event.message;
  
      if (channel === channelName) {
        handleMessage(message); // Unified message handler
      } else {
        console.warn("Received message from unknown channel:", channel);
      }
    };
  
    const handleMessage = (message) => {
      console.log("Received Message:", message);
  
      if (message.command) {
        if (message.command === "LED_ON") {
          updateLEDStatus("LED is ON");
        } else if (message.command === "LED_OFF") {
          updateLEDStatus("LED is OFF");
        } else if (message.command === "PUMP_ON") {
          updatePumpStatus("Pump is ON");
        } else if (message.command === "PUMP_OFF") {
          updatePumpStatus("Pump is OFF");
        } else {
          console.warn("Unknown command:", message.command);
        }
      }
  
      // Handle other sensor data as before
      if (message.temperature !== undefined && message.humidity !== undefined) {
        document.getElementById(
          "temperature_id"
        ).textContent = `${message.temperature.toFixed(1)}°C`;
        document.getElementById(
          "humidity_id"
        ).textContent = `${message.humidity.toFixed(1)}%`;
  
        storeDHT22Data(message.temperature, message.humidity);
      }
  
      if (message.lux !== undefined) {
        document.getElementById("lux_id").textContent = `${message.lux.toFixed(
          1
        )} lux`;
        storeTSL2561Data(message.lux);
      }
  
      if (message.soil_moisture !== undefined) {
        document.getElementById(
          "soil_moisture_id"
        ).textContent = `${message.soil_moisture.toFixed(1)}%`;
        storeSoilMoistureData(message.soil_moisture);
      }
    };
  
    const handleClick = (action, device, duration = null) => {
      const message = { command: `${device}_${action.toUpperCase()}` };
  
      // Add duration if specified and action is "on"
      if (action === "on" && duration) {
        message.duration = duration;
      }
  
      console.log("Publishing message:", message);
      pubnub.publish({
        channel: channelName,
        message: message,
      });
    };
  
    const updateLEDStatus = (status) => {
      statusElement.textContent = `Status: ${status}`;
    };
  
    // Function to update Pump status
    const updatePumpStatus = (status) => {
      pumpStatusElement.textContent = `Status: ${status}`;
    };
  
    const storeDHT22Data = (temperature, humidity) => {
      fetch("https://www.hydrabloom.online/api/store_dht22_data", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ temperature, humidity }),
      })
        .then((response) => response.json())
        .then((data) => console.log("DHT22 data stored:", data))
        .catch((error) => console.error("Error storing DHT22 data:", error));
    };
  
    const storeTSL2561Data = (lux) => {
      fetch("https://www.hydrabloom.online/api/store_tsl2561_data", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ lux }),
      })
        .then((response) => response.json())
        .then((data) => console.log("TSL2561 data stored:", data))
        .catch((error) => console.error("Error storing TSL2561 data:", error));
    };
  
    const storeSoilMoistureData = (soilMoisture) => {
      fetch("https://www.hydrabloom.online/api/store_soil_moisture_data", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ soilMoisture }),
      })
        .then((response) => response.json())
        .then((data) => console.log("Soil moisture data stored:", data))
        .catch((error) =>
          console.error("Error storing soil moisture data:", error)
        );
    };
  
    // Initialize PubNub
    setupPubNub();
  
    // Add event listeners for LED control buttons
    ledOnButton.addEventListener("click", () => handleClick("on", "LED"));
    ledOffButton.addEventListener("click", () => handleClick("off", "LED"));
  
    // Add event listeners for Pump control buttons
    pumpOnButton.addEventListener("click", () => {
      const duration = parseInt(pumpDurationInput.value, 10);
      if (duration && duration > 0) {
        handleClick("on", "PUMP", duration);
      } else {
        alert("Please enter a valid duration in seconds.");
      }
    });
  
    pumpOffButton.addEventListener("click", () => {
      handleClick("off", "PUMP");
    });
  });
  
  function updateTimeAndDayNight() {
    // Get the current time
    const now = new Date();
    const hours = now.getHours();
    const minutes = now.getMinutes().toString().padStart(2, '0'); // Ensure two-digit format
    const seconds = now.getSeconds().toString().padStart(2, '0'); // Ensure two-digit format
    
    // Update the real-time clock
    document.getElementById("currentTime").textContent = `${hours}:${minutes}:${seconds}`;
  
    // Determine the time of day
    let dayOrNight;
    if (hours >= 0 && hours < 6) {
        dayOrNight = "Mid Night";
    } else if (hours >= 6 && hours < 12) {
        dayOrNight = "Morning";
    } else if (hours >= 12 && hours < 18) {
        dayOrNight = "Noon";
    } else {
        dayOrNight = "Evening";
    }
  
    // Update the dayOrNight text
    document.getElementById("dayOrNight").textContent = dayOrNight;
  
    // Repeat every second
    setTimeout(updateTimeAndDayNight, 1000);
  }
  
  function toggleMenu() {
    const mobileMenu = document.getElementById("mobile-menu");
    mobileMenu.classList.toggle("open");
  
    // Optional: Toggle hamburger icon animation
    const hamburger = document.querySelector(".hamburger");
    hamburger.classList.toggle("active");
  }