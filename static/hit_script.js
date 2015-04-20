
// function RJ_generateTaskpage(taskid, workerid)
// {   
//     data[taskId]  = taskid;
//     data[workerid]= workerid;
//     data[msgtype] = "generateTask";
//     ws.send(data);
//     return true;
// }

// function opensocket(workid)
// {
//     console.log("Entered opensocket");



var ws_url = "ws://localhost:8888/websocket?Id="+workid;
ws = new WebSocket(ws_url);
console.log("Websocket created = "+ws_url);

ws.onmessage = function(event)
{
    msg = JSON.parse(event.data)
    if(msg.mode == "idle"){
	alert("DOFJSIFEJWE idle");
    }
    if(msg.mode == "ready"){
	alert("DOFJSIFEJWE ready");
    }
    
    if(msg.mode == "select"){
	alert("DOFJSIFEJWE select");
    }
}
ws.onopen = function(evt)
{
    msg = JSON.parse(event.data);
    alert(msg.mode);
    ws.send(JSON.stringify(msg));
}

ws.onclose = function(evt)
{ 
}
ws.onerror = function(evt)
{
    console.log("Error = " + evt.data);
}
document.getElementById('TodoTask').style.display = 'none';
document.getElementById('Welcome').style.display = 'block';
return;
//}

function FormProcessing() 
{
    console.log("Processing form ...1. Write a function to process data 2. \
        Ask if the brancher wants to do more tasks 3. If its a leafer , wait for supervisor's approval")
    document.getElementById('TodoTask').innerHTML = "Thank you ! Now, wait to supervise your task ";
    //Figure out how to send all teh task info to the server - Replacement for gethandler needed!
    ws.send("AddTasks");
    return 1;
}
