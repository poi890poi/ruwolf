    function trim(strText) {
        // this will get rid of leading spaces
        while (strText.substring(0,1) == ' ')
            strText = strText.substring(1, strText.length);

        // this will get rid of trailing spaces
        while (strText.substring(strText.length-1,strText.length) == ' ')
            strText = strText.substring(0, strText.length-1);

       return strText;
    }

    function createXMLHttpRequest()
    {
        if (window.XMLHttpRequest)
        {// code for IE7+, Firefox, Chrome, Opera, Safari
            xmlhttp = new XMLHttpRequest();
        }
        else
        {// code for IE6, IE5
            xmlhttp = new ActiveXObject("Microsoft.XMLHTTP");
        }
        return xmlhttp;
    }

    function htmlEncode(s)
    {
        return s.replace(/&(?!\w+([;\s]|$))/g, "&amp;")
            .replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }

    function send_text()
    {
        formobj = document.getElementById("EditMessage")
        xmlhttp = createXMLHttpRequest();
        xmlhttp.onreadystatechange = function()
        {
            if (xmlhttp.readyState==4 && xmlhttp.status==204)
            {
                poll();
            }
        }
        params = formobj.value;
        xmlhttp.open("POST", "/send_text/", true);
        xmlhttp.setRequestHeader("Authorization", sessionkey);
        xmlhttp.setRequestHeader("Content-type", "text/plain");
        xmlhttp.setRequestHeader("Content-length", params.length);
        xmlhttp.setRequestHeader("Connection", "close");
        xmlhttp.send(params);
        formobj.value = "";
    }

    function logout()
    {
        $.cookie("702CCBC8-F4A3-11DF-8EFE-4405DFD72085", "", { expires: -1 });
    }

    function login()
    {
        xmlhttp = createXMLHttpRequest();
        xmlhttp.onreadystatechange = function()
        {
            //alert("returned " + xmlhttp.status);
            if (xmlhttp.readyState==4 && xmlhttp.status==200)
            {
                sessionkey = xmlhttp.responseText;
                $.cookie("702CCBC8-F4A3-11DF-8EFE-4405DFD72085", sessionkey, { expires: 7 });
                $("#Login").hide();
                resizeUI();
            }
            else if (xmlhttp.readyState==4 && xmlhttp.status==401)
            {
                alert("password incorrect");
                $("#Login").show();
                resizeUI();
            }
        }
        params = "";
        params += $("#Username").val();
        params += "\r\n";
        params += $("#Password").val();
        xmlhttp.open("POST", "/login/", true);
        xmlhttp.setRequestHeader("Content-type", "text/plain");
        xmlhttp.setRequestHeader("Content-length", params.length);
        xmlhttp.setRequestHeader("Connection", "close");
        xmlhttp.send(params);
    }

    function poll()
    {
        var my_JSON_object = {};
        xmlhttp = createXMLHttpRequest();
        xmlhttp.onreadystatechange = function()
        {
            if (xmlhttp.readyState==4 && xmlhttp.status==200)
            {
                var scr_to_bottom = (($("#MessageList").attr("scrollTop")+
                    $("#MessageList").height()) - $("#MessageList").attr("scrollHeight"));

                var obj = jQuery.parseJSON(xmlhttp.responseText);
                var tmpstring = "<table cellspacing='0'>";
                var i, N = obj.length;
                for (i=0; i<N; i++) {
                    if (obj[i][0] == 0) {
                        var msg = new String();
                        msg += "<tr><td class='header'>";
                        msg += "<span><b>"+obj[i][1]+"</b> at "+obj[i][2]+"<br/></span></td></tr>";
                        msg += "<tr><td class='body'><blockquote>"+obj[i][3]+"</blockquote></td></tr>";
                        msg += "";
                        tmpstring += msg;
                        if (obj[i][4] > timestamp) timestamp = obj[i][4];
                    }
                }
                tmpstring += "</table>";
                $("#MessageList").append(tmpstring);

                // is scroll is at bottom, scroll to bottom
                if (scr_to_bottom >= 0) {
                    $("#MessageList").attr({scrollTop: $("#MessageList").attr("scrollHeight")});
                    //document.getElementById("dbg").innerHTML = scr_to_bottom;
                } else {
                    //document.getElementById("dbg").innerHTML = "don't scroll";
                }
            }
            else if (xmlhttp.readyState==4 && xmlhttp.status==204)
            {
                $("#Login").hide();
                resizeUI();
            }
            else if (xmlhttp.readyState==4 && xmlhttp.status==401)
            {
                $("#Login").show();
                resizeUI();
            }
        }
        params = timestamp + "";
        xmlhttp.open("POST", "/check_update/", true);
        xmlhttp.setRequestHeader("Authorization", sessionkey);
        xmlhttp.setRequestHeader("Content-type", "text/plain");
        xmlhttp.setRequestHeader("Content-length", params.length);
        xmlhttp.setRequestHeader("Connection", "close");
        xmlhttp.send(params);
    }

    function init_poll()
    {
        poll();
        timer = setInterval(poll, 500);
    }