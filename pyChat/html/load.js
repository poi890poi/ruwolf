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
        //var description = "[rnd]";
        //send_text("/host " + description);
        window.location = "./host.html"
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
                if (roomobj[3] == 0) {
                    $("#MnuQuit").addClass("menuitem")
                        .removeClass("menudisable");
                } else {
                    $("#MnuQuit").removeClass("menuitem")
                        .addClass("menudisable");
                }
                if (roomobj[4] == userobj[3]) {
                    ishost = true;
                }
            } else {
                $("#MnuQuit").removeClass("menuitem")
                    .addClass("menudisable");
            }

            if (ishost) {
        		var menu = $("#MenuContainerHost");
                if (roomobj[3] > 0) {
                    $("#MnuReadyCheck").html("Open Game");
                } else {
                    $("#MnuReadyCheck").html("Ready Check");
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
        if (target.length >= 4)
        {
            targetname = target[3];
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
            mitem.html("Vote for <b>" + layoutSafeStr(targetname) + "</b>");
    		mitem.unbind("click");
    		mitem.click(function (e) {
                send_text("/vote_rdy " + targetname);
    		});
        } else if ((userobj[1] & 4) && (phase < 10) && (targetname != userobj[3])) { // game host, USR_HOST
            $("#MnuReport").removeClass("menudisable")
                .addClass("menuitem");
    		var mitem = $("#MnuReport");
            mitem.html("Kick <b>" + layoutSafeStr(targetname) + "</b>");
    		mitem.unbind("click");
    		mitem.click(function (e) {
                send_text("/kick " + targetname);
    		});
        } else if (target.length >= 4) {
            $("#MnuVote").removeClass("menudisable")
                .addClass("menuitem");
            var target_status = target[1];
            var target_role = target[2];
            var target_alignment = target_role & 0x4f000000;
            var self_role = userobj[2];
            var self_alignment = self_role & 0x4f000000;
            if ((userobj[1] & 0x1000) && (target_status & 0x2) && (target_alignment != self_alignment)) { // bite
        		var mitem = $("#MnuVote");
                mitem.html("Attack <b>" + layoutSafeStr(targetname) + "</b>");
        		mitem.unbind("click");
        		mitem.click(function (e) {
                    send_text_ex("/target", 0x1000, targetname);
        		});
            } else {
                return true;
            }
        } else {
            return true;
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
        join.html("Join <b>" + layoutSafeStr(data_json[0]) + "</b>");
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
                txt += "Host: " + data_json[4] + "<br/>";
                txt += "Rule-set: " + data_json[1] + "<br/>";
                txt += "Participant: " + data_json[6] + "<br/><br/>";
                txt += data_json[7];
                $("#Utility #Util2").html(txt);
                //$("#Utility #Util2").html(obj.attr("data-json"));
                resizeUI(0);
            }
        }, 500);
    })
        .live("mouseout", function(e) {
            clearTimeout(t_hover);
            t_hover = setTimeout("general_info();", 500);
        });

    $("#UserList div.clk_user").live("mouseover", function(e) {
        var obj = $(this);

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
            if (data_json.length >= 4)
            {
                $("#Utility #Util2").html(obj.attr("data-json"));
                resizeUI(0);
            }
        }, 500);
    })
        .live("mouseout", function(e) {
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

function general_info()
{
    var txt = "";
    txt += "Latency: " + latency + "<br/>";
    // room (description, ruleset, options, phase, host, roomid, participant, message)
    var roomobj = jQuery.parseJSON(roomjson);
    if (roomobj.length >= 8)
    {
        txt += "Game: " + roomobj[0] + "<br/>";
        txt += "Rule set: " + roomobj[1] + "<br/>";
        txt += "Phase: " + roomobj[3];
        txt += " ("+get_day_night(roomobj[3])+")<br/>";
        txt += "Participant: " + roomobj[6] + "<br/>";
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
        wid = $(window).width() - 300 - save;
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