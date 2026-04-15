-- ── Combat logging: auto-toggle for Mythic+ dungeons ───────────────────────
--
-- Enables WoW's combat log (/combatlog) when a Mythic+ key starts and
-- disables it when the key ends. The resulting WoWCombatLog.txt gets
-- uploaded to warcraftlogs.com via the Warcraft Logs Uploader app, and
-- that's what feeds Umbra's backend ingest.
--
-- Why this exists: forgetting /combatlog before a pull = no data. Having
-- it always on logs overworld/raid activity too, which clutters uploads.
-- Auto-toggling narrows logging to exactly the M+ windows we care about.
--
-- Multi-party note: if multiple people in the party run this addon, they
-- will each produce their own combat log. Uploading all of them is fine
-- — the backend dedups overlapping fights by player/encounter/start-time,
-- so extra uploads only add redundancy, not duplicate data.

local UMBRA_PURPLE = "|cff8a2be2"
local GREEN = "|cff00ff00"
local YELLOW = "|cffffff00"

local function Print(msg)
    if DEFAULT_CHAT_FRAME then
        DEFAULT_CHAT_FRAME:AddMessage(UMBRA_PURPLE .. "Umbra|r: " .. msg)
    end
end

-- Advanced Combat Logging is a separate WoW CVar from /combatlog.
-- Without it the log file is generated but missing player GUIDs and
-- detailed ability data — WCL can't parse such logs and our backend
-- can't score from them. Force it on whenever we start a log.
local function EnsureAdvancedLogging()
    if not GetCVar then return end
    if GetCVar("advancedCombatLogging") ~= "1" then
        SetCVar("advancedCombatLogging", 1)
        Print(YELLOW .. "Enabled Advanced Combat Logging (was off).|r")
    end
end

-- True when we turned logging on ourselves. Used to avoid toggling off
-- a log the user started manually (e.g., for a raid right after a key).
local startedByUs = false

local function EnableLogging()
    EnsureAdvancedLogging()
    if LoggingCombat() then
        -- User already has logging on; don't clobber or take credit.
        startedByUs = false
        return
    end
    LoggingCombat(true)
    startedByUs = true
    Print(GREEN .. "Combat logging enabled for this key.|r")
end

local function DisableLogging()
    if not startedByUs then return end
    if not LoggingCombat() then
        startedByUs = false
        return
    end
    LoggingCombat(false)
    startedByUs = false
    Print(YELLOW .. "Combat logging stopped. Upload via the Warcraft Logs app to feed Umbra.|r")
end

-- CHALLENGE_MODE_START fires the instant the timer starts ticking.
-- CHALLENGE_MODE_COMPLETED fires on timed or depleted finish.
-- CHALLENGE_MODE_RESET fires when the group resets the instance mid-run.
-- PLAYER_LEAVING_WORLD covers "player left the instance" (e.g., hearthed out).
-- PLAYER_LOGIN: one-time setup chance to flip Advanced Combat Logging on.
local logger = CreateFrame("Frame")
logger:RegisterEvent("PLAYER_LOGIN")
logger:RegisterEvent("CHALLENGE_MODE_START")
logger:RegisterEvent("CHALLENGE_MODE_COMPLETED")
logger:RegisterEvent("CHALLENGE_MODE_RESET")
logger:RegisterEvent("PLAYER_LEAVING_WORLD")

logger:SetScript("OnEvent", function(_, event)
    if event == "PLAYER_LOGIN" then
        -- Set the CVar at login regardless of opt-out so the setting
        -- persists between sessions even if the user disabled auto-log.
        EnsureAdvancedLogging()
        return
    end

    if UmbraSettings and UmbraSettings.autoCombatLog == false then
        -- User opted out.
        return
    end

    if event == "CHALLENGE_MODE_START" then
        EnableLogging()
    elseif event == "CHALLENGE_MODE_COMPLETED" or event == "CHALLENGE_MODE_RESET" then
        -- Delay the disable so the CHALLENGE_MODE_END combat-log line has
        -- time to flush to WoWCombatLog.txt. Without this, WCL sees
        -- keystoneTime=0 / kill=false / rating=null even though the key
        -- was completed cleanly — the completion record was cut off.
        if C_Timer and C_Timer.After then
            C_Timer.After(8, DisableLogging)
        else
            DisableLogging()
        end
    elseif event == "PLAYER_LEAVING_WORLD" then
        -- Player left the instance; cut the log immediately — no key in
        -- progress to record completion for.
        DisableLogging()
    end
end)

-- ── Slash command: /umbralog on|off|status ─────────────────────────────────

SLASH_UMBRALOG1 = "/umbralog"
SlashCmdList["UMBRALOG"] = function(msg)
    msg = (msg or ""):lower():gsub("^%s+", ""):gsub("%s+$", "")
    UmbraSettings = UmbraSettings or {}

    if msg == "off" or msg == "disable" then
        UmbraSettings.autoCombatLog = false
        Print("Auto combat logging " .. YELLOW .. "DISABLED|r. Use '/umbralog on' to re-enable.")
    elseif msg == "on" or msg == "enable" then
        UmbraSettings.autoCombatLog = true
        Print("Auto combat logging " .. GREEN .. "ENABLED|r. Keys will auto-log from now on.")
    else
        local state = (UmbraSettings.autoCombatLog == false) and (YELLOW .. "DISABLED|r")
            or (GREEN .. "ENABLED|r")
        local live = LoggingCombat() and (GREEN .. "ON|r") or (YELLOW .. "off|r")
        Print("Auto-log: " .. state .. "  |  Combat log currently: " .. live)
        Print("Commands: /umbralog on  |  /umbralog off")
    end
end
