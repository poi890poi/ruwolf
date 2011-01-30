$(window).load(function(){
    var isIE = (navigator.appName == "Microsoft Internet Explorer");
    if (isIE) {
    } else {
        $(window).bind("focus", function() {
            window_focus = true;
            //$("#Utility #Util2").html("has focus");
        })
            .bind("blur", function() {
                window_focus = false;
                //$("#Utility #Util2").html("no focus");
            });
    }

    $("#UtilityContainer #Util1").click(function(){
        $(this).removeClass("active");
        $(this).addClass("inactive");
        $("#UtilityContainer #Util2").removeClass("inactive");
        $("#UtilityContainer #Util2").addClass("active");
        resizeUI(0);
    });

	$("div.menuitem").live("mouseover", function (e) {
        $(this).addClass("menuhover");
	});
	$("div.menuitem").live("mouseout", function (e) {
        $(this).removeClass("menuhover");
	});
    $(document).click(function(e) {
		$("div.contextmenu").hide();
    });

    $("#MnuHelp").click(function(e) {
        if ($(this).hasClass("menudisable")) return;
		$("div.contextmenu").hide();
        get_dcontent("/help.html");
    });
    $("#MnuQuit").click(function(e) {
        if ($(this).hasClass("menudisable")) return;
		$("div.contextmenu").hide();
        send_text("/quit");
    });
    $("#MnuLogout").live("click", function(e) {
        if ($(this).hasClass("menudisable")) return;
		$("div.contextmenu").hide();
        send_text("/logout");
    });
    $("#MnuHost").live("click", function(e) {
        if ($(this).hasClass("menudisable")) return;
		$("div.contextmenu").hide();
        get_dcontent("/host.html");
        //window.location = "./host.html"
    });
    $("#MnuUserProfile").live("click", function(e) {
        if ($(this).hasClass("menudisable")) return;
		$("div.contextmenu").hide();
        get_dcontent("/profile.html");
        //window.location = "./host.html"
    });
    $("#MnuReadyCheck").click(function(e) {
        if ($(this).hasClass("menudisable")) return;
		$("div.contextmenu").hide();
        send_text("/ready");
    });
    $("#MnuDrop").click(function(e) {
        if ($(this).hasClass("menudisable")) return;
		$("div.contextmenu").hide();
        send_text("/drop");
    });

    $(document)[0].oncontextmenu = function() {return false;}
    $(document).mousedown(function(e){
        if( e.button == 2 ) {
    		$("div.contextmenu").hide();
            if (e.ctrlKey) {
                return true;
            }

            // user status (roomid, user_status[user], role, username)
            //alert(userjson);
            var userobj = jQuery.parseJSON(userjson);
            if (userobj.length < 4)
            {
                return true;
            }

            if (userobj[0]) { // is in room
                $("#MnuLogout").removeClass("menuitem")
                    .addClass("menudisable");
                $("#MnuHost").removeClass("menuitem")
                    .addClass("menudisable");
            } else {
                $("#MnuLogout").removeClass("menudisable")
                    .addClass("menuitem");
                $("#MnuHost").removeClass("menudisable")
                    .addClass("menuitem");
            }

            // room (description, ruleset, options, phase, host, roomid, participant, message)
            //$("#Utility #Util2").html(roomjson);
            //resizeUI(0);

            var roomobj = jQuery.parseJSON(roomjson);
            var ishost = false;
            if (roomobj.length >=5 && userobj.length >= 4)
            {
                if (roomobj[3] == 0 || roomobj[3] >= 0xffff || !(userobj[1] & 0x2)) {
                    $("#MnuQuit").addClass("menuitem")
                        .removeClass("menudisable");
                } else {
                    $("#MnuQuit").removeClass("menuitem")
                        .addClass("menudisable");
                }
                if (roomobj[4] == userobj[3] && roomobj[3] < 0x10) {
                    ishost = true;
                }
            } else {
                $("#MnuQuit").removeClass("menuitem")
                    .addClass("menudisable");
            }

            if (ishost) {
        		var menu = $("#MenuContainerHost");
                if (roomobj[3] >= 0x10 && roomobj[3] < 0xffff) {
                    $("#MnuReadyCheck").removeClass("menuitem")
                        .addClass("menudisable");
                } else {
                    $("#MnuReadyCheck").addClass("menuitem")
                        .removeClass("menudisable");
                    if (roomobj[3] > 0) {
                        $("#MnuReadyCheck").html("開新遊戲");
                    } else {
                        $("#MnuReadyCheck").html("確認開始");
                    }
                }
        		menu.css("left", e.pageX+"px");
        		menu.css("top", e.pageY+"px");
        		setTimeout("$('#MenuContainerHost').show();", 120);
    			return false;
            } else {
        		var menu = $("#MenuContainerGeneral");
        		menu.css("left", e.pageX+"px");
        		menu.css("top", e.pageY+"px");
        		setTimeout("$('#MenuContainerGeneral').show();", 120);
    			return false;
            }
        } else {
            return true;
        }
    });

    $("#UserList div.clk_user").live("click", function(e) {
		$(".contextmenu").hide();

        // user status (roomid, user_status[user], role, username)
        var userobj = jQuery.parseJSON(userjson);
        if (userobj.length < 4)
        {
            return true;
        }

        var targetname = "";
        var target = jQuery.parseJSON($(this).attr('data-json'));
        if (target.length >= 8)
        {
            targetname = target[3];
            t_display = target[7];
        }

        // room (description, ruleset, options, phase, host, roomid, participant)
        var phase = 0;
        var roomid = "";
        var roomobj = jQuery.parseJSON(roomjson);
        if (roomobj.length >= 6)
        {
            phase = roomobj[3];
            roomid = roomobj[5];
        }

        //if ((roomid) && (phase == 1) && (userobj[1] & 256) && (targetname != userobj[3])) { // vote for ready, USR_RDYCHK
        $("#MenuContainerTarget").children(".menuitem").removeClass("menuitem")
            .addClass("menudisable");
        if ((roomid) && (phase == 1) && (userobj[1] & 256)) { // vote for ready, USR_RDYCHK
            $("#MnuVote").removeClass("menudisable")
                .addClass("menuitem");
    		var mitem = $("#MnuVote");
            mitem.html("選擇<b>" + layoutSafeStr(t_display) + "</b>");
    		mitem.unbind("click");
    		mitem.click(function (e) {
                send_text("/vote_rdy " + targetname);
    		});
        } else if (target.length >= 4) {
            var target_status = target[1];
            var target_role = target[2];
            var target_alignment = target_role & 0x4f000000;
            var self_role = userobj[2] & 0x00ffffff;
            var self_alignment = userobj[2] & 0x4f000000;
            if ((userobj[1] & 0x1000) && (target_status & 0x2) && (target_alignment != self_alignment)) { // bite
                $("#MnuVote").removeClass("menudisable")
                    .addClass("menuitem");
        		var mitem = $("#MnuVote");
                mitem.html("選擇咬<b>" + layoutSafeStr(t_display) + "</b>");
        		mitem.unbind("click");
        		mitem.click(function (e) {
                    send_text_ex("/target", 0x1000, targetname);
        		});
            } else if ((userobj[1] & 0x100) && (target_status & 0x2)) { // day vote
                $("#MnuVote").removeClass("menudisable")
                    .addClass("menuitem");
        		var mitem = $("#MnuVote");
                mitem.html("選擇吊死<b>" + layoutSafeStr(t_display) + "</b>");
        		mitem.unbind("click");
        		mitem.click(function (e) {
                    send_text_ex("/target", 0x100, targetname);
        		});
            }

            if ((userobj[1] & 0x2000) && (self_role == 0x200) && (target_status & 0x2) && (target_alignment != self_alignment)) { // blocker
                $("#MnuNightAction").removeClass("menudisable")
                    .addClass("menuitem");
        		var mitem = $("#MnuNightAction");
                mitem.html("魅惑<b>" + layoutSafeStr(t_display) + "</b>");
        		mitem.unbind("click");
        		mitem.click(function (e) {
                    send_text_ex("/target", 0x2000, targetname);
        		});
            } else if ((userobj[1] & 0x8000) && (self_role == 0x1) && (target_status & 0x2) && (userobj[3] != target[3])) { // seer
                $("#MnuNightAction").removeClass("menudisable")
                    .addClass("menuitem");
        		var mitem = $("#MnuNightAction");
                mitem.html("占卜<b>" + layoutSafeStr(t_display) + "</b>");
        		mitem.unbind("click");
        		mitem.click(function (e) {
                    send_text_ex("/target", 0x8000, targetname);
        		});
            } else if ((userobj[1] & 0x4000) && (self_role == 0x2) && (target_status & 0x2) && (userobj[3] != target[3])) { // healer
                $("#MnuNightAction").removeClass("menudisable")
                    .addClass("menuitem");
        		var mitem = $("#MnuNightAction");
                mitem.html("治療<b>" + layoutSafeStr(t_display) + "</b>");
        		mitem.unbind("click");
        		mitem.click(function (e) {
                    send_text_ex("/target", 0x4000, targetname);
        		});
            }
        }

        if ((userobj[1] & 4) && (phase < 0x10) && (targetname != userobj[3])) { // game host, USR_HOST
            $("#MnuReport").removeClass("menudisable")
                .addClass("menuitem");
    		var mitem = $("#MnuReport");
            mitem.html("踢除<b>" + layoutSafeStr(t_display) + "</b>");
    		mitem.unbind("click");
    		mitem.click(function (e) {
                send_text("/kick " + targetname);
    		});
        } else if ((userobj[1] & 4) && (phase >= 0x10) && (targetname != userobj[3])) { // game host, USR_HOST
            $("#MnuReport").removeClass("menudisable")
                .addClass("menuitem");
    		var mitem = $("#MnuReport");
            mitem.html("舉發<b>" + layoutSafeStr(t_display) + "</b>");
    		mitem.unbind("click");
    		mitem.click(function (e) {
                send_text("/report " + targetname);
    		});
        }

		var menu = $("#MenuContainerTarget");
		menu.css("left", e.pageX+"px");
		menu.css("top", e.pageY+"px");
		setTimeout("$('#MenuContainerTarget').show();", 120);
        return false;
    });

    $("#UserList div.clk_room").live("click", function(e) {
		$("div.contextmenu").hide();

        //alert($(this).attr("data-json"));
        // room (description, ruleset, options, phase, host, roomid, participant)
        if (!sessionkey)
        {
            return true;
        }

        var data_json = jQuery.parseJSON($(this).attr("data-json"));
        var roomid = data_json[5];

        if (data_json[3] > 0)
        {
            // not in recruiting
            return true;
        }

		var join = $("#MnuJoin");
        join.html("加入遊戲<b>" + layoutSafeStr(data_json[0]) + "</b>");
		join.unbind("click");
		join.click(function (e) {
            send_text("/join " + roomid);
		});
		var menu = $("#MenuContainerRoom");
		menu.css("left", e.pageX+"px");
		menu.css("top", e.pageY+"px");
		setTimeout("$('#MenuContainerRoom').show();", 120);
        return false;
    });

    $("#UserList div.clk_room").live("mouseover", function(e) {
        var obj = $(this);
        hoverobj = obj;

        // this is for debug
        // in formal release, hover user info is only available when game is not commencing

        clearTimeout(t_hover);
        t_hover = setTimeout(function () {
            //$("#Utility #Util2").html($.dump(obj));
            //resizeUI(0);
            // room (description, ruleset, options, phase, host, roomid, participant, message)
            if (!sessionkey)
            {
                return true;
            }

            var data_json = jQuery.parseJSON(obj.attr("data-json"));
            if (data_json.length >= 8)
            {
                var txt = "";
                txt += "<b>" + data_json[0] + "</b><br/>";
                txt += "主持人：" + data_json[4] + "<br/>";
                txt += "規則：" + data_json[1] + "<br/>";
                txt += "人數：" + data_json[6] + "<br/><br/>";
                txt += data_json[7];
                $("#Utility #Util2").html(txt);
                //$("#Utility #Util2").html(obj.attr("data-json"));
                resizeUI(0);
            }
        }, 500);
    })
        .live("mouseout", function(e) {
            hoverobj = 0;
            clearTimeout(t_hover);
            t_hover = setTimeout("general_info();", 500);
        });

    $("#UserList div.clk_user").live("mouseover", function(e) {
        var obj = $(this);
        hoverobj = obj;

        clearTimeout(t_hover);
        t_hover = setTimeout(function () {
            // $("#Utility #Util2").html($.dump(obj));
            //resizeUI(0);
            // user status (roomid, user_status[user], role, username, ip, hash, email, displayname)
            if (!sessionkey)
            {
                return true;
            }

            var data_json = jQuery.parseJSON(obj.attr("data-json"));
            if (data_json.length >= 8)
            {
                var txt = "";
                txt += "<b>" + data_json[3] + "</b><br/>";
                txt += "Status: 0x" + data_json[1].toString(16) + "<br/>";
                txt += "Role: 0x" + data_json[2].toString(16) + "<br/>";
                txt += "IP: " + data_json[4] + "<br/>";
                txt += "Email: " + data_json[6] + "<br/><br/>";
                $("#Utility #Util2").html(txt);
                resizeUI(0);
            }
        }, 500);
    })
        .live("mouseout", function(e) {
            hoverobj = 0;
            clearTimeout(t_hover);
            t_hover = setTimeout("general_info();", 500);
        });

    general_info();
    resizeUI(0);
    init_poll();

    $(window).resize(function(){
        resizeUI(500);
    });
});

function get_timeout_string(tleft)
{
    var dtobj = new Date();
    dtobj.setTime(tleft);

    var rettxt = "";
    rettxt += dtobj.getUTCHours().toString().padL(2,"0");
    rettxt += ":";
    rettxt += dtobj.getUTCMinutes().toString().padL(2,"0");
    rettxt += ":";
    rettxt += dtobj.getUTCSeconds().toString().padL(2,"0");
    return rettxt;
}

function general_info()
{
    if (hoverobj)
    {
        return;
    }
    var txt = "";
    txt += "Latency: " + latency + "<br/>";
    // room (description, ruleset, options, phase, host, roomid, participant, message)
    var roomobj = jQuery.parseJSON(roomjson);
    if (roomobj.length >= 8)
    {
        txt += "Game: " + roomobj[0] + "<br/>";
        txt += "Rule set: " + roomobj[1] + "<br/>";
        txt += "Phase: 0x" + roomobj[3].toString(16);
        txt += " ("+get_day_night(roomobj[3])+")<br/>";
        txt += "Participant: " + roomobj[6] + "<br/>";
        var now = new Date();
        var tleft = phase_timeout - now.getTime();
        if (tleft < 0) tleft = 0;
        if (tleft > 86400000)
        {
        }
        else if (tleft < 30999)
        {
            txt = "<big>" + get_timeout_string(tleft) + "</big>";
            if (wait_action)
            {
                txt += "<br/>";
                txt += "回合將結束！";
            }
            //$("#Utility #Util2").css("font-size", "48px");
        }
        else
        {
            txt += get_timeout_string(tleft);
            //$("#Utility #Util2").css("font-size", "");
        }
    }
    $("#Utility #Util2").html(txt);
    t_hover = setTimeout("general_info();", 1000);
}

function get_day_night(phase)
{
    if ((phase >> 4 == 0) || (phase > 0xffff))
    {
        return -1;
    }
    return (phase >> 4) % 2
}

function resizeUI(wait)
{
    t_resizeui = setTimeout("resizeUIactual();", wait);
}

function resizeUIactual()
{
    var save = 32;
    var pad = 24;
    var wid = 680;
    if ($(window).width() < 1024)
    {
        wid = $(window).width() - 300 - save - pad;
    }
    if (wid < 450) wid = 450;
    $("#MessageList").width(wid-2);
    $("#PostMessage textarea").width(wid);

    var offset = $("#MessageList").offset();
    offset.left += wid + pad;
    $("#UserList").offset(offset);

    var scr_to_bottom = (($("#MessageList").attr("scrollTop")+
        $("#MessageList").outerHeight()) - $("#MessageList").attr("scrollHeight"));

    var seth = 0;
    var postm = $("#PostMessage").outerHeight();
    var login = 0;
    if ($('#Login').is(':visible')) {
        login = $("#Login").outerHeight();
    }
    seth = $(window).height() - postm - login - save;
    if (seth < 200 ) seth = 200;
    $("#MessageList").height(seth);
    //$("#Toolbar").height($(window).height()-save);

    var utilp = 16;
    var utilh = 0;
    if ($('#Utility').is(':visible')) {
        itemh = $("#Utility #UtilityContainer .active").outerHeight() + save;
        if (itemh > 150) itemh = 250;
        $("#Utility #UtilityContainer").height(itemh);
        utilh = $("#Utility").outerHeight();
    }
    seth = $(window).height() - utilh - save;
    if (seth < 200 ) seth = 200;
    $("#UserList").height(seth-utilp);

    offset.top += $("#UserList").outerHeight() + utilp;
    $("#Utility").offset(offset);

    if (scr_to_bottom >= 0) {
        $("#MessageList").attr({scrollTop: $("#MessageList").attr("scrollHeight")});
    }
}

String.prototype.padL = function(width,pad)
{
    if (!width ||width<1)
    return this;

    if (!pad) pad=" ";

    var length = width - this.length

    if (length < 1)
    return this.substr(0,width);

    return (String.repeat(pad,length) + this).substr(0,width);
}
String.prototype.padR = function(width,pad)
{
    if (!width || width<1)
    return this;

    if (!pad) pad=" ";

    var length = width - this.length

    if (length < 1) this.substr(0,width);
    return (this + String.repeat(pad,length)).substr(0,width);
}
String.repeat = function(chr,count)
{
    var str = "";
    for(var x=0;x<count;x++)
    {
        str += chr
    };
    return str;
}