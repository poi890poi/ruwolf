    var timestamp = 0;
    var sessionkey = $.cookie("702CCBC8-F4A3-11DF-8EFE-4405DFD72085");
    //var sessionkey = ""; //for testing
    var user_status = new Array();

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
            else if (xmlhttp.readyState==4 && xmlhttp.status==205)
            {
                location.reload();
            }
        }
        params = formobj.value;
        trimmed = trim(params);
        if (trimmed == "/logout") {
            xmlhttp.open("POST", "/logout/", true);
            xmlhttp.setRequestHeader("Authorization", sessionkey);
            xmlhttp.setRequestHeader("Content-type", "text/plain");
            xmlhttp.setRequestHeader("Content-length", sessionkey.length);
            xmlhttp.setRequestHeader("Connection", "close");
            xmlhttp.send(sessionkey);
        } else if (trimmed == "/list") {
            list_room();
        } else if (trimmed == "/quit") {
            xmlhttp.open("POST", "/quit/", true);
            xmlhttp.setRequestHeader("Authorization", sessionkey);
            xmlhttp.setRequestHeader("Content-type", "text/plain");
            xmlhttp.setRequestHeader("Content-length", sessionkey.length);
            xmlhttp.setRequestHeader("Connection", "close");
            xmlhttp.send(sessionkey);
        } else if (trimmed.substring(0, 6) == "/host ") {
            var arg = trimmed.split(" ", 2);
            description = "";
            if (arg[1]) {description = arg[1];}
            xmlhttp.open("POST", "/host/", true);
            xmlhttp.setRequestHeader("Authorization", sessionkey);
            xmlhttp.setRequestHeader("Content-type", "text/plain");
            xmlhttp.setRequestHeader("Content-length", description.length);
            xmlhttp.setRequestHeader("Connection", "close");
            xmlhttp.send(description);
        } else if (trimmed.substring(0, 6) == "/join ") {
            var arg = trimmed.split(" ", 2);
            roomid = "";
            if (arg[1]) {roomid = arg[1];}
            xmlhttp.open("POST", "/join/", true);
            xmlhttp.setRequestHeader("Authorization", sessionkey);
            xmlhttp.setRequestHeader("Content-type", "text/plain");
            xmlhttp.setRequestHeader("Content-length", roomid.length);
            xmlhttp.setRequestHeader("Connection", "close");
            xmlhttp.send(roomid);
        } else {
            xmlhttp.open("POST", "/send_text/", true);
            xmlhttp.setRequestHeader("Authorization", sessionkey);
            xmlhttp.setRequestHeader("Content-type", "text/plain");
            xmlhttp.setRequestHeader("Content-length", params.length);
            xmlhttp.setRequestHeader("Connection", "close");
            xmlhttp.send(params);
        }
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
                var obj = jQuery.parseJSON(xmlhttp.responseText);
                sessionkey = obj[0];
                document.title = obj[1];
                $.cookie("702CCBC8-F4A3-11DF-8EFE-4405DFD72085", sessionkey, { expires: 7 });
                $("#Login").fadeOut();
                resizeUI(500);
            }
            else if (xmlhttp.readyState==4 && xmlhttp.status==401)
            {
                alert("password incorrect");
                $("#Login").fadeIn();
                resizeUI(0);
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

    function join_room(roomid) {
        $("#EditMessage").val("/join "+roomid);
    }

    function list_room()
    {
        var my_JSON_object = {};
        xmlhttp = createXMLHttpRequest();
        xmlhttp.onreadystatechange = function()
        {
            if (xmlhttp.readyState==4) {
                if (xmlhttp.status==200)
                {
                    var scr_to_bottom = (($("#MessageList").attr("scrollTop")+
                        $("#MessageList").outerHeight()) - $("#MessageList").attr("scrollHeight"));

                    var obj = jQuery.parseJSON(xmlhttp.responseText);
                    var tmpstring = "<table cellspacing='0'>";
                    var i, N = obj.length;
                    for (i=0; i<N; i++) {
                        if (obj[i][0] == 2) {
                            // room (description, ruleset, options, phase, host)
                            var subobj = jQuery.parseJSON(obj[i][3]);

                            var roomhtml = new String();
                            roomid = "'" + obj[i][1] + "'"
                            roomhtml += "<div class='room' onlick='join(" + roomid + ");'>";
                            roomhtml += subobj[0] + " hosted by " + subobj[4];
                            roomhtml += "</div>";

                            var msg = new String();
                            msg += "<tr><td class='header'>";
                            msg += roomhtml + "</td>";
                            msg += "<td class='time'></td>";
                            msg += "</tr>";
                            msg += "<tr><td class='body' colspan='2'></td></tr>";

                            alert(msg);

                            tmpstring += msg;
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
                else if (xmlhttp.status==204)
                {
                    $("#Login").fadeOut();
                    resizeUI(500);
                }
                else if (xmlhttp.status==401)
                {
                    $("#Login").fadeIn();
                    resizeUI(0);
                }
            }
        }
        params = timestamp + "";
        xmlhttp.open("POST", "/list/", true);
        xmlhttp.setRequestHeader("Authorization", sessionkey);
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
            if (xmlhttp.readyState==4) {
                if (xmlhttp.status==200)
                {
                    var scr_to_bottom = (($("#MessageList").attr("scrollTop")+
                        $("#MessageList").outerHeight()) - $("#MessageList").attr("scrollHeight"));

                    var obj = jQuery.parseJSON(xmlhttp.responseText);
                    var tmpstring = "<table cellspacing='0'>";
                    var i, N = obj.length;
                    for (i=0; i<N; i++) {
                        if (obj[i][0] == 0) {
                            //user message (type, username, isoformat, message, timestamp)
                            var msg = new String();
                            msg += "<tr><td class='header'>";
                            //userspan = $("#3B06037A"+obj[i][1]);
                            //if (userspan.length) {
                            //    msg += userspan.html() + "</td>";;
                            //}
                            //else
                            {
                                msg += "<b>"+obj[i][1]+"</b></td>";
                            }
                            msg += "<td class='time'>"+obj[i][2]+"</td>";
                            //msg += "<td class='header3'></td>";
                            msg += "</tr>";
                            msg += "<tr><td class='body' colspan='2'><blockquote>"+obj[i][3]+"</blockquote></td></tr>";
                            tmpstring += msg;
                        }
                        else if (obj[i][0] == 1) {
                            // user status (roomid, user_status[user])
                            var subobj = jQuery.parseJSON(obj[i][3]);

                            var userhtml = new String();
                            if (subobj[1] & 1) {
                                userhtml += "<img class='usericon' src='villager.png'></img>";
                            } else {
                                userhtml += "<img class='usericon' src='dead.png'></img>";
                            }
                            userhtml += "<b>";
                            userhtml += obj[i][1];
                            userhtml += "</b>";

                            userspan = $("#3B06037A"+obj[i][1]);
                            //alert("#3B06037A"+obj[i][1] + ", " + userspan.length);
                            if (userspan.length) {
                                userspan.html(userhtml);
                            }
                            else
                            {
                                userspan = new String();
                                userspan += "<div id='3B06037A" + obj[i][1] + "' class='user'>" + userhtml + "</div>";
                                $("#tab1").append(userspan);
                            }

                            var msg = new String();
                            msg += "<tr><td class='header'>";
                            msg += "<b>"+obj[i][1] + ", " + obj[i][3]+"</b></td>";
                            msg += "<td class='time'></td>";
                            msg += "</tr>";
                            msg += "<tr><td class='body' colspan='2'></td></tr>";
                            tmpstring += msg;
                        }
                        else if (obj[i][0] == 2) {
                            // room (description, ruleset, options, phase, host)
                            var subobj = jQuery.parseJSON(obj[i][3]);

                            var roomhtml = new String();
                            roomid = obj[i][1];
                            roomhtml += "<div class='joinroom' id='" + roomid + "'>";
                            roomhtml += subobj[0] + " hosted by " + subobj[4];
                            roomhtml += "</div>";

                            var msg = new String();
                            msg += "<tr><td class='header'>";
                            msg += roomhtml + "</td>";
                            msg += "<td class='time'></td>";
                            msg += "</tr>";
                            msg += "<tr><td class='body' colspan='2'></td></tr>";

                            tmpstring += msg;
                        }
                        else if (obj[i][0] == 3) {
                            // user quit, obj[i][3] = username
                            userspan = $("#3B06037A"+obj[i][3]);
                            if (userspan.length) {
                                userspan.remove();
                            }
                        }
                        if (obj[i][4] > timestamp) timestamp = obj[i][4];
                    }
                    tmpstring += "</table>";
                    $("#MessageList").append(tmpstring);

                    $(".joinroom").click(function(){
                        join_room($(this).attr("id"));
                    });

                    // is scroll is at bottom, scroll to bottom
                    if (scr_to_bottom >= 0) {
                        $("#MessageList").attr({scrollTop: $("#MessageList").attr("scrollHeight")});
                        //document.getElementById("dbg").innerHTML = scr_to_bottom;
                    } else {
                        //document.getElementById("dbg").innerHTML = "don't scroll";
                    }
                }
                else if (xmlhttp.status==204)
                {
                    $("#Login").fadeOut();
                    resizeUI(500);
                }
                else if (xmlhttp.status==401)
                {
                    $("#Login").fadeIn();
                    resizeUI(0);
                }

                timer = setTimeout(poll, 500);
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
    }
