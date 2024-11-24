let aliveSecond = 0;
let hearBeatRate = 5000;
let pubnub;
// let appChannel = "xhanhan_pi_channel"
let myChannel = "Hydrabloom_SD3_iot"


function time() {
    let d = new Date();
    let currentSecond = d.getTime();
    if (currentSecond - aliveSecond > hearBeatRate + 1000) {
        document.getElementById("connection_id").innerHTML = "Dead";
    } else {
        document.getElementById("connection_id").innerHTML = "Alive";
    }
    setTimeout('time()', 1000);
}
function keepAlive() {
    fetch('/keep_alive')
        .then(response => {
            if (response.ok) {
                let date = new Date();
                aliveSecond = date.getTime();
                return response.json();
            }
            throw new Error("Server offline");
        })
        // .then(responseJson => {
        //     if (responseJson.motion == 1) {
        //         document.getElementById("motion_id").innerHTML = "Motion";
        //     } else {
        //         document.getElementById("motion_id").innerHTML = "No Motion";
        //     }
        // })
        .catch(error => console.log(error));
    setTimeout('keepAlive()', hearBeatRate);

}
function handleClick(cb) {
    if (cb.checked) {
        value = "on";
    } else {
        value = "off";
    }
    // sendEvent(cb.id + "-" + value);
    publicMessage({"buzzer" : value})
}
// function sendEvent(value) {
//     fetch('/status=' + value, {
//         method: "POST"
//     })
// }

const setupPubNUb = () =>{
    pubnub = new pubnub({
        publishkey:'pub-c-18b517bb-ecb2-4940-badd-117a53aec456',
        subscribekey:'sub-c-7cb4f455-1d58-4487-81d5-460d437b7daf',
        userId:"hydrabloom_Web_App",
    })
    //creat a channel
    const channer = pubnub.channel(myChannel);
    //create a subscription
    const subscription = channel.subscription();

    pubnub.addListener({
        status:(s) =>{
            console.log('Status',s.category);
        },
    })

    subscription.onMessage = (messageEvent) =>{
        handleMessage(messageEvent.message);

    }
    subscription.subscribe();

};

const publishMessage = async(message) =>{
    const publishPayload = {
        channel:myChannel,
        message:message,
    };
    await pubnub.publish(publishPayload)
} 

function handleMessage(message){
    if(message == '"Motion":"Yes"'){
        document.getElementById("motion_id").innerHTML = "Yes";

    }
    if(message == '"Motion":"No"'){
        document.getElementById("motion_id").innerHTML = "No";
        
    }
}