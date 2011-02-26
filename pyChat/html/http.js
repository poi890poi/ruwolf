    var SYSTEM_USER = 'aaedddbf-13a9-402b-8ab2-8b0073b3ebf3'
    var ALIGNMENT_MASK = 0xffffff

    var timestamp = 0;
    var sessionkey = $.cookie("702CCBC8-F4A3-11DF-8EFE-4405DFD72085");
    //var sessionkey = ""; //for testing
    var userjson = "[]";
    var wait_action = false;
    var roomjson = "[]";
    var poll_xmlhttp = createXMLHttpRequest();
    var poll_timer;
    var send_xmlhttp = createXMLHttpRequest();
    var login_xmlhttp = createXMLHttpRequest();
    var window_focus = true;
    var t_resizeui;
    var ondemand_xmlhttp = createXMLHttpRequest();
    var credential_xmlhttp = createXMLHttpRequest();
    var dcontent_xmlhttp = createXMLHttpRequest();
    var t_hover;
    var latency = 0;
    var poll_sent = 0;
    var hoverobj = 0;
    var phase_timeout = 9999999999999;
    var isdcontent = false;

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
    
    function handle_credentail_return()
    {
        if (credential_xmlhttp.readyState==4)
        {
            if (credential_xmlhttp.status==202) // username exist
            {
                $("#RegisterOrLogin").attr("value", "登入");
            } else {
                $("#RegisterOrLogin").attr("value", "註冊");
            }
            $("#RegisterOrLogin").attr("disabled", false);

            credential_xmlhttp.onreadystatechange = nill;
            credential_xmlhttp.abort();
        }
    }
    
    function check_credential()
    {
        if (credential_xmlhttp.readyState != 0) {
            return;
        }
        var username = $("#Username").val();
        var password = $("#Password").val();
        // to-do: add validation here, use regular expression maybe
        if (username.length && password.length)
        {
            if (validate_email(username) )
            {
                credential_xmlhttp.onreadystatechange = handle_credentail_return;
                credential_xmlhttp.open("POST", "/check_credential", true);
                credential_xmlhttp.setRequestHeader("Authorization", sessionkey);
                credential_xmlhttp.setRequestHeader("Content-type", "text/plain");
                credential_xmlhttp.send(username);
                return;
            }
        }
        $("#RegisterOrLogin").attr("disabled", true);
    }

    function validate_email(str) {
        if (/^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$/.test(str)){
            return true;
        }
        return false;
    }

    function resetContent()
    {
        isdcontent = false;
        $("#MessageList").empty();
        $("#UserListContainer").empty();
        userjson = "[]";
        wait_action = false;
        roomjson = "[]";
        timestamp = 0;
        poll_xmlhttp.onreadystatechange = nill;
        poll_xmlhttp.abort();
        poll();
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
                //location.reload();
                resetContent();
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
        } else if (trimmed == "/slogout") {
            $.cookie("702CCBC8-F4A3-11DF-8EFE-4405DFD72085", "", { expires: -1 });
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
            wait_action = false;
        }
    }

    function send_text_ex(params, action, content)
    {
        if (send_xmlhttp.readyState != 0) {
            return;
        }
        send_xmlhttp.onreadystatechange = handle_send_return;
        var trimmed = trim(params);

        if (trimmed == "/target") {
            send_xmlhttp.open("POST", trimmed, true);
            send_xmlhttp.setRequestHeader("Authorization", sessionkey);
            send_xmlhttp.setRequestHeader("Content-type", "text/plain");
            send_xmlhttp.setRequestHeader("X-Action", action);
            send_xmlhttp.send(content);
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
                //document.title = obj[1];
                $.cookie("702CCBC8-F4A3-11DF-8EFE-4405DFD72085", sessionkey, { expires: 7 });
                $("#Login").fadeOut();
                resizeUI(500);
            }
            else if (login_xmlhttp.status==401)
            {
                alert("密碼錯誤！");
                $("#Login").fadeIn();
                resizeUI(0);
            }

            login_xmlhttp.onreadystatechange = nill;
            login_xmlhttp.abort();
            
            resetContent();
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
    
    function handle_dcontent_return() {
        if (dcontent_xmlhttp.readyState==4)
        {
            if (dcontent_xmlhttp.status==200)
            {
                isdcontent = true;
                $("#MessageList").html(dcontent_xmlhttp.responseText);
                // scroll to top
                $("#MessageList").attr({scrollTop: 0});
            }

            dcontent_xmlhttp.onreadystatechange = nill;
            dcontent_xmlhttp.abort();
        }
    }
    
    function get_dcontent(dcontent) {
        // get dynamic content
        if (dcontent_xmlhttp.readyState != 0) {
            return;
        }
        dcontent_xmlhttp.onreadystatechange = handle_dcontent_return;
        dcontent_xmlhttp.open("POST", "dcontent", true);
        dcontent_xmlhttp.setRequestHeader("Authorization", sessionkey);
        dcontent_xmlhttp.setRequestHeader("Content-type", "text/plain");
        dcontent_xmlhttp.send(dcontent);
    }

    function handle_poll_return()
    {
        if (poll_xmlhttp.readyState==4) {
            var dtobj = new Date();
            latency = dtobj.getTime() - poll_sent;

            if (poll_xmlhttp.status==200 && poll_xmlhttp.responseText.length)
            {
                var scr_to_bottom = (($("#MessageList").attr("scrollTop")+
                    $("#MessageList").outerHeight()) - $("#MessageList").attr("scrollHeight"));

                var obj = jQuery.parseJSON(poll_xmlhttp.responseText);
                var msgappend = "";
                var lstappend = "";
                var tbdom = $("#UserList #UserListContainer");

                var i, N = obj.length;
                for (i=0; i<N; i++) {
                    if (obj[i][0] == 0) {
                        //user message (type, username, isoformat, message, timestamp, phase)
                        var msg = new String();
                        var daynight = get_day_night(obj[i][5]);
                        if (obj[i][1] == SYSTEM_USER) {
                            if (daynight == 1) {
                                msg += "<tr><td colspan='2' class='system_night'>";
                            } else {
                                msg += "<tr><td colspan='2' class='system'>";
                            }
                            msg += obj[i][3] + "</td></tr>";
                            msgappend += msg;
                        } else {
                            if (daynight == 1) {
                                msg += "<tr class='night'><td>";
                            } else {
                                msg += "<tr><td>";
                            }
                            var username = layoutSafeStr(obj[i][1]);
                            msg += "<b>" + username + "</b></td>";
                            msg += "<td>" + obj[i][3] + "</td></tr>";
                            msgappend += msg;
                        }
                    } else if (obj[i][0] == 0x9000) {
                        //user message (type, username, isoformat, message, timestamp, phase)
                        var msg = new String();
                        var daynight = get_day_night(obj[i][5]);
                        if (daynight == 1) {
                            msg += "<tr><td colspan='2' class='system_night'>";
                        } else {
                            msg += "<tr><td colspan='2' class='system'>";
                        }
                        msg += obj[i][3] + "</td></tr>";
                        msgappend += msg;
                    }
                    else if (obj[i][0] == 1 || obj[i][0] == 0x4000 || obj[i][0] == 5 || obj[i][0] == 0x1000) {
                        // user status (roomid, user_status[user], role, username, ip, hash, email, displayname)

                        var subobj = jQuery.parseJSON(obj[i][3]);
                        //if (obj[i][0] == 0x1000) alert(subobj[2]);

                        if (obj[i][0] == 0x4000) { // user status private
                            if (subobj[1] & 16) { // kicked, USR_KICKED
                                alert("你被邀請到大廳了！");
                                send_text("/drop_confirm");
                            }
                            userjson = obj[i][3];

                            wait_action = false;
                            var userobj = jQuery.parseJSON(userjson);
                            if (userobj.length >= 2)
                            {
                                if (userobj[1] & 0xfff00)
                                {
                                    wait_action = true;
                                }
                            }
                        }

                        var phase = 0;
                        var roomobj = jQuery.parseJSON(roomjson);
                        if (roomobj.length >= 8)
                        {
                            phase = roomobj[3]
                        }

                        var userhtml = new String();
                        //alert(obj[i][3]);
                        if (subobj[1] & 1) { // connection alive
                            if (phase >= 0x10)
                            {
                                if (subobj[1] & 0x2) {
                                    if ((subobj[2] & ALIGNMENT_MASK) == 0x100) {
                                        userhtml += "<img class='usericon' src='images/rolewolf.png'></img>";
                                    } else if ((subobj[2] & ALIGNMENT_MASK) == 0x200) {
                                        userhtml += "<img class='usericon' src='images/blocker.png'></img>";
                                    } else if ((subobj[2] & ALIGNMENT_MASK) == 0x01) {
                                        userhtml += "<img class='usericon' src='images/eye.png'></img>";
                                    } else if ((subobj[2] & ALIGNMENT_MASK) == 0x02) {
                                        userhtml += "<img class='usericon' src='images/heal.png'></img>";
                                    } else if ((subobj[2] & ALIGNMENT_MASK) == 0x04) {
                                        userhtml += "<img class='usericon' src='images/villager.png'></img>";
                                    } else {
                                        userhtml += "<img class='usericon' src='images/unknown.png'></img>";
                                    }
                                } else if (subobj[1] & 0x20) {
                                    userhtml += "<img class='usericon' src='images/hang.png'></img>";
                                } else {
                                    userhtml += "<img class='usericon' src='images/dead.png'></img>";
                                }
                            } else {
                                if ((subobj[1] & 256) && subobj[0]) { // waiting for ready check
                                    userhtml += "<img class='usericon' src='images/error.png'></img>";
                                } else if (subobj[1] & 2) { // ipconflict
                                    userhtml += "<img class='usericon' src='images/possession.png'></img>";
                                } else if (subobj[1] & 4) { // host
                                    userhtml += "<img class='usericon' src='images/mod.png'></img>";
                                } else {
                                    userhtml += "<img class='usericon' src='images/villager.png'></img>";
                                }
                            }
                        } else {
                            userhtml += "<img class='usericon' src='images/error.png'></img>";
                        }
                        if (obj[i][0] == 0x4000) userhtml += "<u>";
                        userhtml += "<b>";
                        userhtml += layoutSafeStr(subobj[7]);
                        userhtml += "</b>";
                        if (obj[i][0] == 0x4000) userhtml += "</u>";

                        userspan = tbdom.find("#3B06037A"+subobj[5]);
                        if (userspan.length) {
                            userspan.html(userhtml);
                            userspan.attr('data-json', obj[i][3]);
                        } else {
                            userspan = new String();
                            userspan += "<div id='3B06037A" + subobj[5] + "' class='clk_user clkable' data-json='" + obj[i][3] + "'>"
                            userspan += userhtml + "</div>";
                            tbdom.append(userspan);
                            //lstappend += userspan;
                        }
                    }
                    else if (obj[i][0] == 2) {
                        // room (description, ruleset, options, phase, host, roomid, participant, message)
                        // in lobby
                        var subobj = jQuery.parseJSON(obj[i][3]);
                        if (subobj.length >= 8)
                        {
                            //alert(obj[i][3]);
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
                        // MSG_ROOM_DETAIL
                        // room (description, ruleset, options, phase, host, roomid, participant, message)
                        // in game
                        var subobj = jQuery.parseJSON(obj[i][3]);
                        if (subobj.length >= 8)
                        {
                            roomjson = obj[i][3];
                            var daynight = get_day_night(subobj[3]);
                            if (daynight == 0) {
                                //$("body").removeClass("night");
                                //$("body").addClass("day");
                            } else if (daynight == 1) {
                                //$("body").removeClass("day");
                                //$("body").addClass("night");
                            }
                            general_info();
                            resizeUI(0);
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
                    else if (obj[i][0] == 0x10000) {
                        //setTimeout("location.reload();", 500);
                        //alert('reset');
                        resetContent();
                        return;
                    }
                    else if (obj[i][0] == 9) {
                        // time left before phase timeout
                        var now = new Date();
                        phase_timeout = now.getTime() + parseInt(obj[i][3]);
                    }
                    if (obj[i][4] > timestamp) timestamp = obj[i][4];
                }

                if (msgappend) {
                    var tbmsglist = $("#MessageList #TableMessageList");
                    if (tbmsglist.length)
                    {
                        tbmsglist.append(msgappend);
                    } else {
                        msgappend = "<table id='TableMessageList' cellspacing='0'><tr><th class='left'></th><th></th></tr>" + msgappend;
                        msgappend += "</table>";
                        $("#MessageList").append(msgappend);
                    }
                    setTimeout(function () {
                        // notification
                        //if (!window_focus) {alert("new msg");}
                    }, 500);
                }

                if (lstappend) {
                    tbdom.append(lstappend);
                }

                if (isdcontent)
                {
                }
                else if (scr_to_bottom >= 0) {
                    // if scroll is not at bottom, scroll to bottom
                    $("#MessageList").attr({scrollTop: $("#MessageList").attr("scrollHeight")});
                }
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

        var dtobj = new Date();
        poll_sent = dtobj.getTime();
    }

    function init_poll()
    {
        poll();
    }