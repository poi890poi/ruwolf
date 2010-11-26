    var timestamp = 0;
    var sessionkey = $.cookie("702CCBC8-F4A3-11DF-8EFE-4405DFD72085");
    //var sessionkey = ""; //for testing
    var user_status = new Array();
    var polling = false;

    function trim(strText) {
        // this will get rid of leading spaces
        while (strText.substring(0,1) == ' ')
            strText = strText.substring(1, strText.length);

        // this will get rid of trailing spaces
        while (strText.substring(strText.length-1,strText.length) == ' ')
            strText = strText.substring(0, strText.length-1);

        // replace multiple spaces with single one
        strText = strText.replace(/ {2,}/g,' ');

        return strText;
    }

    function layoutSafeStr(strText)
    {
        if (strText.length > 12) {
            return strText.substring(0, 9) + "...";
        }
        return strText;
    }

    function createXMLHttpRequest()
    {
        var xmlhttp;
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

    function send_text(params)
    {
        if (!params)
        {
            params = $("#EditMessage").val();
            $("#EditMessage").val("");
        }
        var xmlhttp = createXMLHttpRequest();
        xmlhttp.onreadystatechange = function()
        {
            if (xmlhttp.readyState==4 && xmlhttp.status==204)
            {
                poll();
                // may cause double fetch problem if polling is already sent
            }
            else if (xmlhttp.readyState==4 && xmlhttp.status==205)
            {
                location.reload();
            }
        }
        var trimmed = trim(params);
        if (trimmed == "/logout") {
            xmlhttp.open("POST", "/logout/", true);
            xmlhttp.setRequestHeader("Authorization", sessionkey);
            xmlhttp.setRequestHeader("Content-type", "text/plain");
            xmlhttp.send(sessionkey);
        } else if (trimmed == "/quit") {
            xmlhttp.open("POST", "/quit/", true);
            xmlhttp.setRequestHeader("Authorization", sessionkey);
            xmlhttp.setRequestHeader("Content-type", "text/plain");
            xmlhttp.send(sessionkey);
        } else if (trimmed.substring(0, 6) == "/host ") {
            var arg = trimmed.split(" ", 2);
            var description = "";
            if (arg[1]) {description = arg[1];}
            xmlhttp.open("POST", "/host/", true);
            xmlhttp.setRequestHeader("Authorization", sessionkey);
            xmlhttp.setRequestHeader("Content-type", "text/plain");
            xmlhttp.send(description);
        } else if (trimmed.substring(0, 6) == "/join ") {
            var arg = trimmed.split(" ", 2);
            var roomid = "";
            if (arg[1]) {roomid = arg[1];}
            xmlhttp.open("POST", "/join/", true);
            xmlhttp.setRequestHeader("Authorization", sessionkey);
            xmlhttp.setRequestHeader("Content-type", "text/plain");
            xmlhttp.send(roomid);
        } else {
            xmlhttp.open("POST", "/send_text/", true);
            xmlhttp.setRequestHeader("Authorization", sessionkey);
            xmlhttp.setRequestHeader("Content-type", "text/plain");
            xmlhttp.send(params);
        }
    }

    function logout()
    {
        $.cookie("702CCBC8-F4A3-11DF-8EFE-4405DFD72085", "", { expires: -1 });
    }

    function login()
    {
        var xmlhttp = createXMLHttpRequest();
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
        var params = "";
        params += $("#Username").val();
        params += "\r\n";
        params += $("#Password").val();
        xmlhttp.open("POST", "/login/", true);
        xmlhttp.setRequestHeader("Content-type", "text/plain");
        xmlhttp.send(params);
    }

    function join_room(roomid) {
        $("#EditMessage").val("/join "+roomid);
    }

    function poll()
    {
        if (polling == true) {
            return;
        }
        polling = true;
        var my_JSON_object = {};
        var xmlhttp = createXMLHttpRequest();
        xmlhttp.onreadystatechange = function()
        {
            if (xmlhttp.readyState==4) {
                polling = false;
                if (xmlhttp.status==200)
                {
                    var scr_to_bottom = (($("#MessageList").attr("scrollTop")+
                        $("#MessageList").outerHeight()) - $("#MessageList").attr("scrollHeight"));

                    var obj = jQuery.parseJSON(xmlhttp.responseText);
                    var msgappend = "";
                    var lstappend = "";
                    var i, N = obj.length;
                    for (i=0; i<N; i++) {
                        if (obj[i][0] == 0) {
                            //user message (type, username, isoformat, message, timestamp)
                            var msg = new String();
                            msg += "<tr><td class='lead'>";
                            var username = layoutSafeStr(obj[i][1]);
                            msg += "<b>" + username + "</b></td>";
                            msg += "<td>" + obj[i][3] + "</td></tr>";
                            msgappend += msg;
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
                            userhtml += layoutSafeStr(obj[i][1]);
                            userhtml += "</b>";

                            userspan = $("#3B06037A"+obj[i][1]);
                            //alert("#3B06037A"+obj[i][1] + ", " + userspan.length);
                            if (userspan.length) {
                                userspan.html(userhtml);
                            }
                            else
                            {
                                userspan = new String();
                                userspan += "<div id='3B06037A" + obj[i][1] + "' class=''>" + userhtml + "</div>";
                                lstappend += userspan;
                            }
                        }
                        else if (obj[i][0] == 2) {
                            // room (description, ruleset, options, phase, host, roomid, participant)
                            var subobj = jQuery.parseJSON(obj[i][3]);
                            if (subobj.length == 7)
                            {
                                roomid = obj[i][1];

                                var roomhtml = new String();

                                roomhtml += "<b>";
                                roomhtml += subobj[0];
                                roomhtml += "(";
                                roomhtml += subobj[6];
                                roomhtml += ")";
                                roomhtml += "</b>";

                                roomspan = $("#81D995F6"+roomid);
                                if (roomspan.length) {
                                    roomspan.html(roomhtml);
                                    roomspan.attr('data-json', obj[i][3]);
                                }
                                else
                                {
                                    roomspan = new String();
                                    roomspan += "<div id='81D995F6" + roomid + "' class='clk_room clkable' data-json='" + obj[i][3] + "'>"
                                    roomspan += roomhtml + "</div>";
                                    lstappend += roomspan;
                                }
                            }
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

                    if (msgappend) {
                        msgappend = "<table cellspacing='0'>" + msgappend;
                        msgappend += "</table>";
                        $("#MessageList").append(msgappend);
                    }

                    if (lstappend) {
                        lstappend = "<div>" + lstappend;
                        lstappend += "</div>";
                        $("#tab1").append(lstappend);
                    }

                    // is scroll is at bottom, scroll to bottom
                    if (scr_to_bottom >= 0) {
                        $("#MessageList").attr({scrollTop: $("#MessageList").attr("scrollHeight")});
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

                var timer = setTimeout(poll, 500);
            }
        }
        var params = timestamp + "";
        xmlhttp.open("POST", "/check_update/", true);
        xmlhttp.setRequestHeader("Authorization", sessionkey);
        xmlhttp.setRequestHeader("Content-type", "text/plain");
        xmlhttp.send(params);
    }

    function init_poll()
    {
        poll();
    }