# init variables

INTERVAL_SEC = 1000
INTERVAL_MIN = 60 * INTERVAL_SEC
INTERVAL_HOUR = 60 * INTERVAL_MIN
INTERVAL_SHORT = 3 * INTERVAL_SEC
INTERVAL_LONG = 30 * INTERVAL_SEC
INTERVAL_DROPUSER = 12 * INTERVAL_MIN
TIME_MAX = long(9999999999999)

# message types, specified in user column
SYSTEM_USER = 'aaedddbf-13a9-402b-8ab2-8b0073b3ebf3'
GUID_0 = '3e5cdec2-f504-4474-ba0f-2f358c210be8'
GUID_0 = '7051262e-c2ff-4e69-b2ed-76cb4d01eb9a'
GUID_0 = '87018045-fd87-4f7c-ad87-94b9c898cdfe'
GUID_0 = '4b89497a-2bb1-4234-9747-cd7c862479be'
GUID_0 = '9fe94f24-4e45-4cc6-b030-6363d2e7cc1f'
GUID_0 = '8f4c6b3e-0aa8-4d41-a550-95a8e7dd04e0'
GUID_0 = 'a745ee66-6538-48e2-97f1-9eaf32ce5701'
GUID_0 = '1df5fd0f-06eb-4961-a96e-27e78567eb98'
GUID_0 = 'ceb7d84e-f5c2-4f9b-9700-a1d3c63c771e'
GUID_0 = '204c4a4e-5b67-4745-b104-9f6dcf0ad8e4'

# message types
MSG_USER_STATUS = 1
MSG_ROOM = 2
MSG_USERQUIT = 3
MSG_USR_STA_ALIGNMENT = 5
MSG_GAMEDROP = 6
MSG_GAMEDROP_P = 7
MSG_ROOM_DETAIL = 8

MSG_SEER_RESULT = 0x1000
MSG_USR_STA_PRIVATE = 0x4000
MSG_PRIVATE = 0x9000
MSG_PRIVATE_MASK = 0xff000 # match username when fetching

MSG_RELOAD = 0x10000
MSG_ONETIME_MASK = 0xf0000 # if ever fetched by user, remove the entry

# user makr (meta-game status)
USR_CONN = 0x00000001
USR_IPCONFLICT = 0x00000002
USR_HOST = 0x00000004
USR_EMAILCONFIRMED = 0x00000008
USR_KICKED = 0x00000010

# user status
USR_PUBLIC_MASK = 0x00000fff
USR_PRIVATE_MASK = 0x00fff000
USR_ACT_MASK = 0x000fff00
USR_DAY_ACT_MASK = 0x00000f00
USR_NIGHT_ACT_MASK = 0x000ff000
USR_DETECTED_MASK = 0x00f00000

USR_CONN = 0x00000001
USR_SURVIVE = 0x00000002
USR_HOST = 0x00000004
USR_PRESERVE = 0x00000008
USR_KICKED = 0x00000010
USR_LYNCH = 0x00000020
USR_DEADLOCKED_E = 0x00000040
USR_PRESERVE = 0x00000080

USR_DAY_VOTE = 0x00000100
USR_PRESERVE = 0x00000200
USR_PRESERVE = 0x00000400
USR_PRESERVE = 0x00000800

USR_NIGHT_VOTE = 0x00001000
USR_NIGHT_BLOCK = 0x00002000
USR_NIGHT_HEAL = 0x00004000
USR_NIGHT_SEER = 0x00008000
USR_NIGHT_ACT4 = 0x00010000
USR_PRESERVE = 0x00020000
USR_PRESERVE = 0x00040000
USR_PRESERVE = 0x00080000

USR_TARGET1 = 0x00100000
USR_TARGET2 = 0x00200000
USR_TARGET3 = 0x00400000
USR_TARGET4 = 0x00800000

# roles
ROLE_ALIGNMENT_SHIFT = 24

ROLE_SEER = 0x00000001
ROLE_HEALER = 0x00000002
ROLE_HUNTER = 0x00000003
ROLE_VILLAGER = 0x00000004

ROLE_CUPID = 0x00000010
ROLE_LOVER = 0x00000020

ROLE_BITE_MASK = 0x00000f00

ROLE_WOLF = 0x00000100
ROLE_BLOCKER = 0x00000200
ROLE_ALPHA_WOLF = 0x00000300

ROLE_POSSESSION = 0x000001000
ROLE_JUNIOR_WOLF = 0x00002000

# privileges
PVG_ALIGNMENT_MASK = 0x4f000000

PVG_ROOMCHAT = 0x00000001

PVG_DAYCHAT = 0x00000010
PVG_NIGHTCHAT = 0x00000020
PVG_CHAT0 = 0x00000040
PVG_CHAT1 = 0x00000080

PVG_TARGET1 = 0x00100000
PVG_TARGET2 = 0x00200000
PVG_TARGET3 = 0x00400000
PVG_TARGET4 = 0x00800000

PVG_PRIVATE = 0x4fffffff

# rule options

RLE_NIGHTZERO = 0x00000001
RLE_SHOWDEAD = 0x00000002
RLE_VOTE_RUNOFF = 0x00000004
RLE_SKIPLYNCH = 0x00000008
RLE_SELFVOTE = 0x00000010
RLE_NIGHTTALK = 0x00000020
RLE_NIGHTVOTE_AGREE = 0x00000040
RLE_IPCFLT_UNIQUE = 0x00000080
RLE_IPCFLT_DOMAIN = 0x00000100

# do later actions
DLTR_COMMIT_DB = 0b00000001 # obsoleted, use conn.total_changes

# actions
ACT_VOTE_RDY = 1