
function RJ_generateTaskpage(taskid, workerid)
{   
    data[taskId]  = taskid;
    data[workerid]= workerid;
    data[msgtype] = "generateTask";
    ws.send(data);
    return true;
}

function opensocket(workid)
{
	console.log("Entered opensocket");
	var ws_url = "wss://localhost:8888/websocket?Id="+workid;
	ws = new WebSocket(ws_url);
    console.log("Websocket created = "+ws_url);

    ws.onmessage = function(evt)
    {
    	data = evt.data;
    	console.log("message event: "+ data)
        if(data.indexOf("GenPage") >= 0)
        {
           console.log("generateTask msg received");
            document.getElementById('TodoTask').style.display = 'block';
            document.getElementById('Welcome').style.display = 'none';
        }
         if(data.indexOf("WakeUp") >= 0)
         {
            document.getElementById('TodoTask').style.display = 'block';
            document.getElementById('Welcome').style.display = 'none';

         }
    }
    ws.onopen = function(evt)
    {
        console.log("Open socket");
    }

    ws.onclose = function(evt)
    {
        console.log("Closing socket");   
    }
    ws.onerror = function(evt)
    {
        console.log("Error = " + evt.data);
    }
    document.getElementById('TodoTask').style.display = 'none';
    document.getElementById('Welcome').style.display = 'block';
    return;
}

function FormProcessing() 
{
    console.log("Processing form ...1. Write a function to process data 2. \
        Ask if the brancher wants to do more tasks 3. If its a leafer , wait for supervisor's approval")
    document.getElementById('TodoTask').innerHTML = "Thank you ! Now, wait to supervise your task ";
    //Figure out how to send all teh task info to the server - Replacement for gethandler needed!
    ws.send("AddTasks");
    return 1;
}