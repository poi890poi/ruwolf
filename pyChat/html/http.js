    var timestamp = 0;
    var sessionkey = $.cookie("702CCBC8-F4A3-11DF-8EFE-4405DFD72085");
    //var sessionkey = ""; //for testing
    var userjson = "[]";
    var roomjson = "[]";
    var SYSTEM_USER = 'aaedddbf-13a9-402b-8ab2-8b0073b3ebf3'
    var poll_xmlhttp = createXMLHttpRequest();
    var poll_timer;
    var send_xmlhttp = createXMLHttpRequest();
    var login_xmlhttp = createXMLHttpRequest();

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

    function handle_send_return()
    {
        if (send_xmlhttp.readyState==4)
        {
            if (send_xmlhttp.status==204)
            {
                poll();
                // may cause double fetch problem if polling is already sent
            }
            else if (send_xmlhttp.status==205)
            {
                location.reload();
            }
            else if (send_xmlhttp.status==401)
            {
            }

            send_xmlhttp.onreadystatechange = nill;
            send_xmlhttp.abort();
        }
    }

    function send_text(params)
    {
        //alert(send_xmlhttp.readyState);
        if (send_xmlhttp.readyState != 0) {
            return;
        }
        if (!params)
        {
            params = $("#EditMessage").val();
            $("#EditMessage").val("");
        }
        send_xmlhttp.onreadystatechange = handle_send_return;
        var trimmed = trim(params);

        if (trimmed == "/logout" || trimmed == "/quit")
        {
            roomjson = "[]";
        }

        if (trimmed == "/logout" ||
            trimmed == "/quit" ||
            trimmed == "/ready" ||
            trimmed == "/drop_confirm" ||
            trimmed == "/drop") {
            send_xmlhttp.open("POST", trimmed, true);
            send_xmlhttp.setRequestHeader("Authorization", sessionkey);
            send_xmlhttp.setRequestHeader("Content-type", "text/plain");
            send_xmlhttp.send(sessionkey);
        } else if (trimmed.substring(0, 6) == "/host ") {
            var arg = trimmed.split(" ", 2);
            var description = "";
            if (arg[1]) {description = arg[1];}
            send_xmlhttp.open("POST", "/host", true);
            send_xmlhttp.setRequestHeader("Authorization", sessionkey);
            send_xmlhttp.setRequestHeader("Content-type", "text/plain");
            send_xmlhttp.send(description);
        } else if (trimmed.substring(0, 10) == "/vote_rdy ") {
            var arg = trimmed.split(" ", 2);
            var target = "";
            if (arg[1]) {target = arg[1];}
            send_xmlhttp.open("POST", "/vote_rdy", true);
            send_xmlhttp.setRequestHeader("Authorization", sessionkey);
            send_xmlhttp.setRequestHeader("Content-type", "text/plain");
            send_xmlhttp.send(target);
        } else if (trimmed.substring(0, 6) == "/kick ") {
            var arg = trimmed.split(" ", 2);
            var target = "";
            if (arg[1]) {target = arg[1];}
            send_xmlhttp.open("POST", "/kick", true);
            send_xmlhttp.setRequestHeader("Authorization", sessionkey);
            send_xmlhttp.setRequestHeader("Content-type", "text/plain");
            send_xmlhttp.send(target);
        } else if (trimmed.substring(0, 6) == "/join ") {
            var arg = trimmed.split(" ", 2);
            var roomid = "";
            if (arg[1]) {roomid = arg[1];}
            send_xmlhttp.open("POST", "/join", true);
            send_xmlhttp.setRequestHeader("Authorization", sessionkey);
            send_xmlhttp.setRequestHeader("Content-type", "text/plain");
            send_xmlhttp.send(roomid);
        } else {
            send_xmlhttp.open("POST", "/send_text", true);
            send_xmlhttp.setRequestHeader("Authorization", sessionkey);
            send_xmlhttp.setRequestHeader("Content-type", "text/plain");
            send_xmlhttp.send(params);
        }

        if (trimmed == "/logout") {
            $.cookie("702CCBC8-F4A3-11DF-8EFE-4405DFD72085", "", { expires: -1 });
            sessionkey = "";
            userjson = "[]";
        }
    }

    function handle_login_return()
    {
        //alert("returned " + login_xmlhttp.status);
        if (login_xmlhttp.readyState==4)
        {
            if (login_xmlhttp.status==200)
            {
                var obj = jQuery.parseJSON(login_xmlhttp.responseText);
                sessionkey = obj[0];
                document.title = obj[1];
                $.cookie("702CCBC8-F4A3-11DF-8EFE-4405DFD72085", sessionkey, { expires: 7 });
                $("#Login").fadeOut();
                resizeUI(500);
            }
            else if (login_xmlhttp.status==401)
            {
                alert("password incorrect");
                $("#Login").fadeIn();
                resizeUI(0);
            }

            login_xmlhttp.onreadystatechange = nill;
            login_xmlhttp.abort();
        }
    }

    function login()
    {
        if (login_xmlhttp.readyState != 0) {
            return;
        }
        login_xmlhttp.onreadystatechange = handle_login_return;
        var params = "";
        params += $("#Username").val();
        params += "\r\n";
        params += $("#Password").val();
        login_xmlhttp.open("POST", "/login", true);
        login_xmlhttp.setRequestHeader("Content-type", "text/plain");
        login_xmlhttp.send(params);
    }

    function join_room(roomid) {
        $("#EditMessage").val("/join "+roomid);
    }

    function handle_poll_return()
    {
        if (poll_xmlhttp.readyState==4) {
            if (poll_xmlhttp.status==200)
            {

var dtobj = new Date();
var start = dtobj.getTime();

                var scr_to_bottom = (($("#MessageList").attr("scrollTop")+
                    $("#MessageList").outerHeight()) - $("#MessageList").attr("scrollHeight"));

                var obj = jQuery.parseJSON(poll_xmlhttp.responseText);
                var msgappend = "";
                var lstappend = "";
                var tbdom = $("#tab1");

                var i, N = obj.length;
                for (i=0; i<N; i++) {
                    if (obj[i][0] == 0) {
                        //user message (type, username, isoformat, message, timestamp)
                        var msg = new String();
                        if (obj[i][1] == SYSTEM_USER) {
                            msg += "<tr><td colspan='2' class='system'>";
                            msg += obj[i][3] + "</td></tr>";
                            msgappend += msg;
                        } else {
                            msg += "<tr><td class='lead'>";
                            var username = layoutSafeStr(obj[i][1]);
                            msg += "<b>" + username + "</b></td>";
                            msg += "<td>" + obj[i][3] + "</td></tr>";
                            msgappend += msg;
                        }
                    }
                    else if (obj[i][0] == 1 || obj[i][0] == 4 || obj[i][0] == 5) {
                        // user status (roomid, user_status[user], role, username)
                        var subobj = jQuery.parseJSON(obj[i][3]);

                        if (obj[i][0] == 4) { // user status private
                            if (subobj[1] & 16) { // kicked, USR_KICKED
                                alert("You have been INVITED to the lobby.");
                                send_text("/drop_confirm");
                            }
                            userjson = obj[i][3];
                        }

                        var userhtml = new String();
                        //alert(obj[i][3]);
                        if (subobj[1] & 1) { // connection alive
                            if (subobj[1] & 256) { // waiting for ready check
                                userhtml += "<img class='usericon' src='images/unknown.png'></img>";
                            } else if (subobj[1] & 4) { // host
                                userhtml += "<img class='usericon' src='images/mod.png'></img>";
                            //} else if (subobj[2]) { // for test only
                                //userhtml += "<img class='usericon' src='images/rolewolf.png'></img>";
                            } else {
                                userhtml += "<img class='usericon' src='images/villager.png'></img>";
                            }
                        } else {
                            userhtml += "<img class='usericon' src='images/unknown.png'></img>";
                        }
                        if (obj[i][0] == 4) userhtml += "<u>";
                        userhtml += "<b>";
                        userhtml += layoutSafeStr(obj[i][1]);
                        userhtml += "</b>";
                        if (obj[i][0] == 4) userhtml += "</u>";

                        userspan = tbdom.find("#3B06037A"+obj[i][1]);
                        //alert("#3B06037A"+obj[i][1] + ", " + userspan.length);
                        if (userspan.length) {
                            userspan.html(userhtml);
                            userspan.attr('data-json', obj[i][3]);
                        } else {
                            userspan = new String();
                            userspan += "<div id='3B06037A" + obj[i][1] + "' class='clk_user clkable' data-json='" + obj[i][3] + "'>"
                            userspan += userhtml + "</div>";
                            tbdom.append(userspan);
                            //lstappend += userspan;
                        }
                    }
                    else if (obj[i][0] == 2) {
                        // room (description, ruleset, options, phase, host, roomid, participant)
                        var subobj = jQuery.parseJSON(obj[i][3]);
                        if (subobj.length == 7)
                        {
                            roomid = obj[i][1];

                            var roomhtml = new String();
                            if (subobj[3] == 0) { // recruiting
                                roomhtml += "<img class='usericon' src='images/roomopen.png'></img>";
                            } else { // commencing
                                roomhtml += "<img class='usericon' src='images/roomclosed.png'></img>";
                            }

                            roomhtml += "<b>";
                            roomhtml += subobj[0];
                            roomhtml += "(";
                            roomhtml += subobj[6];
                            roomhtml += ")";
                            roomhtml += "</b>";

                            //alert(roomhtml);

                            roomspan = tbdom.find("#81D995F6"+roomid);
                            if (roomspan.length) {
                                roomspan.html(roomhtml);
                                roomspan.attr('data-json', obj[i][3]);
                            } else {
                                //alert(obj[i][3]);
                                roomspan = new String();
                                roomspan += "<div id='81D995F6" + roomid + "' class='clk_room clkable' data-json='" + obj[i][3] + "'>"
                                roomspan += roomhtml + "</div>";
                                lstappend += roomspan;
                            }
                        }
                    }
                    else if (obj[i][0] == 8) {
                        // room (description, ruleset, options, phase, host, roomid, participant)
                        var subobj = jQuery.parseJSON(obj[i][3]);
                        if (subobj.length == 7)
                        {
                            roomjson = obj[i][3];
                        }
                    }
                    else if (obj[i][0] == 3) {
                        // user quit, obj[i][3] = username
                        userspan = $("#3B06037A"+obj[i][3]);
                        if (userspan.length) {
                            userspan.remove();
                        }
                    }
                    else if (obj[i][0] == 6) {
                        // gamedrop, to lobby, obj[i][3] = roomid
                        userspan = $("#81D995F6"+obj[i][3]);
                        if (userspan.length) {
                            userspan.remove();
                        }
                    }
                    else if (obj[i][0] == 7) {
                        alert("The game is dropped by host.");
                        // gamedrop, to room, obj[i][3] = roomid
                        send_text("/quit");
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

dtobj = new Date();
//alert(dtobj.getTime()-start);

            }
            else if (poll_xmlhttp.status==204)
            {
                if ($('#Login').is(':visible')) {
                    $("#Login").fadeOut();
                    resizeUI(500);
                }
            }
            else if (poll_xmlhttp.status==401)
            {
                if (!$('#Login').is(':visible')) {
                    $("#Login").fadeIn();
                    resizeUI(0);
                }
            }

            poll_xmlhttp.onreadystatechange = nill;
            poll_xmlhttp.abort();
            poll_timer = setTimeout(poll, 500);
        }
    }

    function nill(){}

    function poll()
    {
        if (poll_xmlhttp.readyState != 0) {
            return;
        }
        var my_JSON_object = {};
        poll_xmlhttp.onreadystatechange = handle_poll_return;
        var params = timestamp + "";
        poll_xmlhttp.open("POST", "/check_update", true);
        poll_xmlhttp.setRequestHeader("Authorization", sessionkey);
        poll_xmlhttp.setRequestHeader("Content-type", "text/plain");
        poll_xmlhttp.send(params);
    }

    function init_poll()
    {
        poll();
    }