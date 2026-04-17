-- Umbra.gg Stats Panel
-- Opens with /umbra command

local ADDON_PATH = "Interface\\AddOns\\Umbra\\textures\\"
-- Two-column layout: left = grade + stat rows (existing), right = settings.
-- LEFT_COL_WIDTH is pinned so stat rows and the grade stack don't drift when
-- the overall frame is widened.
local LEFT_COL_WIDTH = 360
local RIGHT_COL_WIDTH = 300
local FRAME_WIDTH = LEFT_COL_WIDTH + RIGHT_COL_WIDTH
-- Tall enough for 8 stat rows under the profile card + footer. Healer is the
-- max-row case (6 categories + dps_ilvl + timed_pct).
local FRAME_HEIGHT = 512

-- ── Main Frame ──────────────────────────────────────────────────────────────

local UmbraFrame = CreateFrame("Frame", "UmbraMainFrame", UIParent, "BackdropTemplate")
UmbraFrame:SetSize(FRAME_WIDTH, FRAME_HEIGHT)
UmbraFrame:SetPoint("CENTER")
UmbraFrame:SetMovable(true)
UmbraFrame:EnableMouse(true)
UmbraFrame:RegisterForDrag("LeftButton")
UmbraFrame:SetScript("OnDragStart", UmbraFrame.StartMoving)
UmbraFrame:SetScript("OnDragStop", UmbraFrame.StopMovingOrSizing)
UmbraFrame:SetFrameStrata("HIGH")
UmbraFrame:Hide()

UmbraFrame:SetBackdrop({
    bgFile = "Interface\\DialogFrame\\UI-DialogBox-Background-Dark",
    edgeFile = "Interface\\DialogFrame\\UI-DialogBox-Border",
    tile = true, tileSize = 32, edgeSize = 24,
    insets = { left = 5, right = 5, top = 5, bottom = 5 },
})
UmbraFrame:SetBackdropColor(0.04, 0.01, 0.07, 0.97)

-- Close button
local closeBtn = CreateFrame("Button", nil, UmbraFrame, "UIPanelCloseButton")
closeBtn:SetPoint("TOPRIGHT", UmbraFrame, "TOPRIGHT", -2, -2)

-- ── Header ──────────────────────────────────────────────────────────────────

local headerIcon = UmbraFrame:CreateTexture(nil, "ARTWORK")
headerIcon:SetSize(26, 26)
headerIcon:SetPoint("TOPLEFT", UmbraFrame, "TOPLEFT", 14, -12)
headerIcon:SetTexture("Interface\\AddOns\\Umbra\\textures\\logo.tga")
-- Our logo fills the texture (no square-icon trim needed), so use the
-- default full 0..1 coords instead of the spell-icon border crop.

local titleText = UmbraFrame:CreateFontString(nil, "OVERLAY")
titleText:SetPoint("LEFT", headerIcon, "RIGHT", 8, 0)
titleText:SetFont("Fonts\\FRIZQT__.TTF", 16, "OUTLINE")
titleText:SetText("|cffffffffWoW|r|cff8a2be2Umbra|r|cffffffff.gg|r")

-- ── Profile Card (portrait + role / class / ilvl / grade) ──────────────────
-- Replaces the old glow/starburst/ring visual. Portrait on the left, stacked
-- info on the right. Role and class color follow WoW's class-color palette.

local profileCard = CreateFrame("Frame", nil, UmbraFrame)
profileCard:SetSize(LEFT_COL_WIDTH - 28, 128)
profileCard:SetPoint("TOPLEFT", UmbraFrame, "TOPLEFT", 14, -44)

-- Full 3D character model (same renderer Blizzard uses for the paperdoll).
-- PlayerModel picks up the player's transmog/equipment automatically. Sized
-- taller than wide so the whole body fits inside the profile card.
local portrait = CreateFrame("PlayerModel", nil, profileCard)
portrait:SetSize(112, 124)
portrait:SetPoint("TOPLEFT", profileCard, "TOPLEFT", 2, -2)

-- No backdrop behind the model — let it float on the main panel backdrop
-- so the silhouette reads cleanly without a hard black square.

-- Configure the camera + animation. Call from a deferred hook so it runs
-- after PLAYER_ENTERING_WORLD — SetUnit before login data is ready silently
-- no-ops and leaves an empty scene.
local function _refreshPortraitModel()
    portrait:ClearModel()
    portrait:SetUnit("player")
    portrait:SetPortraitZoom(0)          -- 0 = full body, 1 = face close-up
    portrait:SetFacing(math.rad(18))     -- slight 3/4 turn for silhouette
    portrait:SetAnimation(0)             -- idle stance
end

-- Right-side info stack, anchored to portrait's right edge.
local roleClassText = profileCard:CreateFontString(nil, "OVERLAY")
roleClassText:SetPoint("TOPLEFT", portrait, "TOPRIGHT", 14, -2)
roleClassText:SetFont("Fonts\\FRIZQT__.TTF", 14, "OUTLINE")
roleClassText:SetJustifyH("LEFT")

local ilvlText = profileCard:CreateFontString(nil, "OVERLAY")
ilvlText:SetPoint("TOPLEFT", roleClassText, "BOTTOMLEFT", 0, -4)
ilvlText:SetFont("Fonts\\FRIZQT__.TTF", 12, "")
ilvlText:SetTextColor(0.82, 0.82, 0.82)

-- Grade — big, bold, bottom-right of the card, with a soft radial glow
-- behind it so the letter pops regardless of backdrop.
local gradeGlow = profileCard:CreateTexture(nil, "BACKGROUND", nil, 1)
gradeGlow:SetSize(130, 130)
gradeGlow:SetPoint("BOTTOMRIGHT", profileCard, "BOTTOMRIGHT", 14, -20)
gradeGlow:SetTexture("Interface\\GLUES\\MODELS\\UI_HUMAN\\GenericGlow64")
gradeGlow:SetBlendMode("ADD")
gradeGlow:SetAlpha(0.55)

local gradeText = profileCard:CreateFontString(nil, "OVERLAY")
gradeText:SetPoint("BOTTOMRIGHT", profileCard, "BOTTOMRIGHT", -12, 2)
gradeText:SetFont("Fonts\\FRIZQT__.TTF", 50, "OUTLINE, THICKOUTLINE")
gradeText:SetShadowOffset(3, -3)
gradeText:SetShadowColor(0, 0, 0, 1)
gradeText:SetJustifyH("RIGHT")

-- Re-render the 3D model when the character loads in, swaps gear, or the
-- model changes (transmog, appearance). Calling before PEW can no-op, so
-- PEW is the canonical entry point for the first render.
local portraitRefresh = CreateFrame("Frame")
portraitRefresh:RegisterEvent("PLAYER_ENTERING_WORLD")
portraitRefresh:RegisterEvent("UNIT_MODEL_CHANGED")
portraitRefresh:RegisterEvent("PLAYER_EQUIPMENT_CHANGED")
portraitRefresh:SetScript("OnEvent", function(_, event, unit)
    if event == "UNIT_MODEL_CHANGED" and unit ~= "player" then return end
    _refreshPortraitModel()
end)

-- ── Stat Row Builder ────────────────────────────────────────────────────────

local STAT_ICONS = {
    dps_perf = "Interface\\Icons\\ability_warrior_bladestorm",
    dps_ilvl = nil, -- Set dynamically from spec
    throughput = "Interface\\Icons\\spell_holy_flashheal",
    utility = "Interface\\Icons\\spell_frost_chainsofice",
    survivability = "Interface\\Icons\\spell_holy_ashestoashes",
    cd_usage = "Interface\\Icons\\spell_nature_timestop",
    cpm = "Interface\\Icons\\spell_nature_astralrecalgroup",
    timed_pct = "Interface\\Icons\\inv_misc_key_15",
}

-- Spec icons (matches WCL spec names)
local SPEC_ICONS = {
    -- Warrior
    ["Arms"] = "Interface\\Icons\\ability_warrior_savageblow",
    ["Fury"] = "Interface\\Icons\\ability_warrior_innerrage",
    ["Protection"] = "Interface\\Icons\\ability_warrior_defensivestance",
    -- Paladin
    ["Holy"] = "Interface\\Icons\\spell_holy_holybolt",
    ["Retribution"] = "Interface\\Icons\\spell_holy_auraoflight",
    -- Hunter
    ["Beast Mastery"] = "Interface\\Icons\\ability_hunter_bestialdiscipline",
    ["Marksmanship"] = "Interface\\Icons\\ability_hunter_focusedaim",
    ["Survival"] = "Interface\\Icons\\ability_hunter_camouflage",
    -- Rogue
    ["Assassination"] = "Interface\\Icons\\ability_rogue_deadlybrew",
    ["Outlaw"] = "Interface\\Icons\\ability_rogue_rollthebones",
    ["Subtlety"] = "Interface\\Icons\\ability_stealth",
    -- Priest
    ["Discipline"] = "Interface\\Icons\\spell_holy_powerwordshield",
    ["Shadow"] = "Interface\\Icons\\spell_shadow_shadowwordpain",
    -- Death Knight
    ["Blood"] = "Interface\\Icons\\spell_deathknight_bloodpresence",
    ["Frost"] = "Interface\\Icons\\spell_deathknight_frostpresence",
    ["Unholy"] = "Interface\\Icons\\spell_deathknight_unholypresence",
    -- Shaman
    ["Elemental"] = "Interface\\Icons\\spell_nature_lightning",
    ["Enhancement"] = "Interface\\Icons\\spell_shaman_improvedstormstrike",
    ["Restoration"] = "Interface\\Icons\\spell_nature_magicimmunity",
    -- Mage
    ["Arcane"] = "Interface\\Icons\\spell_holy_magicalsentry",
    ["Fire"] = "Interface\\Icons\\spell_fire_firebolt02",
    -- Warlock
    ["Affliction"] = "Interface\\Icons\\spell_shadow_deathcoil",
    ["Demonology"] = "Interface\\Icons\\spell_shadow_metamorphosis",
    ["Destruction"] = "Interface\\Icons\\spell_shadow_rainoffire",
    -- Monk
    ["Brewmaster"] = "Interface\\Icons\\spell_monk_brewmaster_spec",
    ["Mistweaver"] = "Interface\\Icons\\spell_monk_mistweaver_spec",
    ["Windwalker"] = "Interface\\Icons\\spell_monk_windwalker_spec",
    -- Druid
    ["Balance"] = "Interface\\Icons\\spell_nature_starfall",
    ["Feral"] = "Interface\\Icons\\ability_druid_catform",
    ["Guardian"] = "Interface\\Icons\\ability_racial_bearform",
    -- Demon Hunter
    ["Havoc"] = "Interface\\Icons\\ability_demonhunter_specdps",
    ["Vengeance"] = "Interface\\Icons\\ability_demonhunter_spectank",
    -- Evoker
    ["Devastation"] = "Interface\\Icons\\classicon_evoker_devastation",
    ["Preservation"] = "Interface\\Icons\\classicon_evoker_preservation",
    ["Augmentation"] = "Interface\\Icons\\classicon_evoker_augmentation",
}

-- Labels reflect what the backend engine actually scores on.
-- "vs %s" suffix only where the score is a spec-ranked WCL percentile;
-- the other categories are absolute benchmarks, not spec-relative.
local STAT_LABELS_MAP = {
    dps_perf      = "DPS vs %s",
    dps_ilvl      = "DPS vs %s (iLvl)",
    throughput    = "HPS vs %s",
    utility       = "Utility (kicks/dispels)",
    survivability = "Survivability",
    cd_usage      = "Cooldown usage",
    cpm           = "Casts per minute",
    timed_pct     = "Keys timed",
}

-- Render order per role — mirrors the backend's role-weighted priorities.
-- Healer leads with healing_throughput because that's their headline metric
-- (tied for top weight 0.20 with damage and utility). DPS/Tank lead with
-- damage_output (their highest-weight category). `dps_ilvl` is shown last
-- among damage stats since it's display-only, not part of the composite.
local STAT_ORDER_FOR_ROLE = {
    dps    = { "dps_perf", "dps_ilvl", "utility", "survivability", "cd_usage", "cpm", "timed_pct" },
    healer = { "throughput", "dps_perf", "dps_ilvl", "utility", "survivability", "cd_usage", "cpm", "timed_pct" },
    tank   = { "dps_perf", "dps_ilvl", "utility", "survivability", "cd_usage", "cpm", "timed_pct" },
}

-- Match Core.lua + frontend/lib/grades.ts. D is amber (#ffcc00), F is red (#ff3030).
local GRADE_COLORS = {
    ["S+"] = {1, 0.5, 0}, ["S"] = {1, 0.5, 0},
    ["A+"] = {0.64, 0.21, 0.93}, ["A"] = {0.64, 0.21, 0.93}, ["A-"] = {0.64, 0.21, 0.93},
    ["B+"] = {0, 0.44, 0.87}, ["B"] = {0, 0.44, 0.87}, ["B-"] = {0, 0.44, 0.87},
    ["C+"] = {0.12, 1, 0}, ["C"] = {0.12, 1, 0}, ["C-"] = {0.12, 1, 0},
    ["D+"] = {1, 0.8, 0}, ["D"] = {1, 0.8, 0}, ["D-"] = {1, 0.8, 0},
    ["F"] = {1, 0.19, 0.19}, ["F-"] = {1, 0.19, 0.19},
}

-- Bar / value colors tuned to the wowumbra.gg palette:
--   ≥80  lilac   (#c084fc — on-primary-container, the site's "excellent" tone)
--   ≥60  cyan    (#22d3ee — site's secondary accent)
--   ≥40  amber   (#fbbf24 — readable warning on the dark backdrop)
--   <40  coral   (#f87171 — site's tertiary / error tone)
local function GetStatColorRGB(v)
    if v >= 80 then return 0.753, 0.518, 0.988
    elseif v >= 60 then return 0.133, 0.827, 0.933
    elseif v >= 40 then return 0.984, 0.749, 0.141
    else return 0.973, 0.443, 0.443
    end
end

local function RGBToHex(r, g, b)
    return string.format("%02x%02x%02x", r * 255, g * 255, b * 255)
end

local ROW_WIDTH = LEFT_COL_WIDTH - 32
local ROW_HEIGHT = 32
local ICON_SIZE = 36

local function CreateStatRow(parent, yOffset)
    -- Main row container (offset right to make room for icon overlap)
    local row = CreateFrame("Frame", nil, parent)
    row:SetSize(ROW_WIDTH, ROW_HEIGHT)
    row:SetPoint("TOPLEFT", parent, "TOPLEFT", 28, yOffset)

    -- Pill-shaped dark background
    local bg = row:CreateTexture(nil, "BACKGROUND")
    bg:SetAllPoints()
    bg:SetTexture(ADDON_PATH .. "bar_bg")

    -- Fill bar (pill-shaped, colored by score)
    local bar = CreateFrame("StatusBar", nil, row)
    bar:SetSize(ROW_WIDTH, ROW_HEIGHT)
    bar:SetPoint("LEFT")
    bar:SetMinMaxValues(0, 100)
    bar:SetValue(0)
    bar:SetStatusBarTexture(ADDON_PATH .. "bar")
    bar:SetStatusBarColor(0.54, 0.17, 0.89, 0.5)

    -- Overlay frame for text (above the bar)
    local overlay = CreateFrame("Frame", nil, row)
    overlay:SetAllPoints()
    overlay:SetFrameLevel(row:GetFrameLevel() + 3)

    -- Circular icon frame (overlaps left edge of pill)
    local iconFrame = CreateFrame("Frame", nil, parent)
    iconFrame:SetSize(ICON_SIZE, ICON_SIZE)
    iconFrame:SetPoint("LEFT", row, "LEFT", -ICON_SIZE / 2 + 4, 0)
    iconFrame:SetFrameLevel(row:GetFrameLevel() + 4)

    -- Icon ring background
    local iconRing = iconFrame:CreateTexture(nil, "BACKGROUND")
    iconRing:SetAllPoints()
    iconRing:SetTexture(ADDON_PATH .. "icon_ring")

    -- Icon itself
    local icon = iconFrame:CreateTexture(nil, "ARTWORK")
    icon:SetSize(ICON_SIZE - 10, ICON_SIZE - 10)
    icon:SetPoint("CENTER")
    icon:SetTexCoord(0.07, 0.93, 0.07, 0.93)

    -- Label text
    local label = overlay:CreateFontString(nil, "OVERLAY")
    label:SetPoint("LEFT", row, "LEFT", 22, 0)
    label:SetFont("Fonts\\FRIZQT__.TTF", 12, "")
    label:SetTextColor(1, 1, 1)
    label:SetShadowOffset(1, -1)
    label:SetShadowColor(0, 0, 0, 1)

    -- Value text
    local value = overlay:CreateFontString(nil, "OVERLAY")
    value:SetPoint("RIGHT", row, "RIGHT", -10, 0)
    value:SetFont("Fonts\\FRIZQT__.TTF", 13, "OUTLINE")

    return {
        frame = row,
        iconFrame = iconFrame,
        bar = bar,
        icon = icon,
        label = label,
        value = value,
    }
end

local statRows = {}
-- Profile card occupies y = -44 to -172 (taller to fit the 3D model +
-- bigger grade). Start stat rows with a breathing gap below it.
-- 8 rows: healer can render 6 categories + dps_ilvl + timed_pct.
local rowStartY = -184
for i = 1, 8 do
    statRows[i] = CreateStatRow(UmbraFrame, rowStartY - (i - 1) * (ROW_HEIGHT + 6))
end

-- ── "Open on web" button ───────────────────────────────────────────────────
-- WoW sandboxes URL opening, so the button doesn't launch a browser directly.
-- It shows a small popup with a read-only, pre-selected EditBox containing
-- the player's wowumbra.gg profile URL. User does Ctrl-C, alt-tabs, and
-- pastes in their browser. Lowest-friction we can do inside the client.

local function _buildProfileUrl()
    -- Region: prefer the portal CVar (returns "us", "eu", "kr", "tw", "cn").
    -- Falls back to "us" if the CVar isn't available (custom clients, etc).
    local region = (GetCVar and GetCVar("portal")) or "us"
    region = tostring(region):lower()

    -- Realm: use the normalized form (no spaces, mixed case stripped in the
    -- site's URL handling). GetNormalizedRealmName matches how the Lua
    -- database keys players.
    local realm = GetNormalizedRealmName and GetNormalizedRealmName() or GetRealmName()
    realm = realm or "Unknown"

    local name = UnitName("player") or "Unknown"

    -- URL-encode spaces and non-ASCII. The site decodes realm/name on the
    -- server side, so a permissive escape is fine.
    local function urlEncode(s)
        return (s:gsub("([^%w%-_.~])", function(c)
            return string.format("%%%02X", string.byte(c))
        end))
    end

    return string.format(
        "https://wowumbra.gg/player/%s/%s/%s",
        urlEncode(region),
        urlEncode(realm),
        urlEncode(name)
    )
end

-- Register a popup dialog once. Shown via StaticPopup_Show("UMBRA_OPEN_ON_WEB").
StaticPopupDialogs["UMBRA_OPEN_ON_WEB"] = {
    text = "Copy this URL and open it in your browser:",
    button1 = CLOSE,
    hasEditBox = true,
    editBoxWidth = 320,
    OnShow = function(self)
        local eb = self.editBox or self.EditBox
        if not eb then return end
        eb:SetText(_buildProfileUrl())
        eb:HighlightText()
        eb:SetFocus()
    end,
    EditBoxOnEscapePressed = function(self) self:GetParent():Hide() end,
    EditBoxOnEnterPressed = function(self) self:GetParent():Hide() end,
    timeout = 0,
    whileDead = true,
    hideOnEscape = true,
    preferredIndex = 3,
}

-- Footer button anchored to the bottom of the left column.
local openWebBtn = CreateFrame("Button", nil, UmbraFrame, "UIPanelButtonTemplate")
openWebBtn:SetSize(200, 22)
openWebBtn:SetPoint("BOTTOM", UmbraFrame, "BOTTOMLEFT", LEFT_COL_WIDTH / 2, 14)
openWebBtn:SetText("Open full profile on wowumbra.gg")
openWebBtn:SetScript("OnClick", function()
    StaticPopup_Show("UMBRA_OPEN_ON_WEB")
end)
openWebBtn:SetScript("OnEnter", function(self)
    GameTooltip:SetOwner(self, "ANCHOR_TOP")
    GameTooltip:AddLine("|cffffffffWoW|r|cff8a2be2Umbra|r|cffffffff.gg|r")
    GameTooltip:AddLine("Shows your full profile URL in a popup.", 1, 1, 1)
    GameTooltip:AddLine("WoW can't open browsers, so copy + paste.", 0.7, 0.7, 0.7)
    GameTooltip:Show()
end)
openWebBtn:SetScript("OnLeave", function() GameTooltip:Hide() end)

-- ── Refresh ─────────────────────────────────────────────────────────────────

-- Role icon atlas strings (reusable — pull outside RefreshUI so we don't
-- recreate the table every refresh).
local ROLE_ICON = {
    tank = "|TInterface\\LFGFrame\\UI-LFG-ICON-PORTRAITROLES:16:16:0:0:64:64:0:19:22:41|t",
    healer = "|TInterface\\LFGFrame\\UI-LFG-ICON-PORTRAITROLES:16:16:0:0:64:64:20:39:1:20|t",
    dps = "|TInterface\\LFGFrame\\UI-LFG-ICON-PORTRAITROLES:16:16:0:0:64:64:20:39:22:41|t",
}

-- Infer the current player's role from their spec if the backend data is
-- missing. GetSpecializationRole returns "TANK", "HEALER", or "DAMAGER".
local function _currentPlayerRole()
    local specIdx = GetSpecialization and GetSpecialization() or nil
    if not specIdx then return "dps" end
    local r = GetSpecializationRole and GetSpecializationRole(specIdx) or nil
    if r == "TANK" then return "tank"
    elseif r == "HEALER" then return "healer"
    else return "dps" end
end

-- Paint the profile card header with a best-effort view: prefer backend
-- data but always fall back to what WoW knows locally so the card never
-- renders blank for a not-yet-graded player.
local function _paintProfile(myData)
    local _, classToken = UnitClass("player")
    local classInfo = classToken and C_ClassColor and C_ClassColor.GetClassColor(classToken) or nil
    local classColor = classInfo and classInfo:GenerateHexColor() or "ffffffff"
    local localizedClass = UnitClass("player") or "Unknown"

    local role = (myData and myData.role) or _currentPlayerRole()
    local spec = (myData and myData.spec) or (function()
        local idx = GetSpecialization and GetSpecialization()
        if idx then
            local _, n = GetSpecializationInfo(idx)
            return n
        end
    end)() or ""

    local roleIcon = ROLE_ICON[role] or ""
    local classLine = spec ~= "" and (spec .. " " .. localizedClass) or localizedClass
    roleClassText:SetText(roleIcon .. " |c" .. classColor .. classLine .. "|r")

    local _, equipped = GetAverageItemLevel()
    ilvlText:SetText(string.format("Item Level %.1f", equipped or 0))

    if myData and myData.grade then
        local gc = GRADE_COLORS[myData.grade] or {1, 1, 1}
        gradeText:SetText(myData.grade)
        gradeText:SetTextColor(gc[1], gc[2], gc[3])
        gradeGlow:SetVertexColor(gc[1], gc[2], gc[3])
        gradeGlow:SetAlpha(0.55)
    else
        gradeText:SetText("N/R")
        gradeText:SetTextColor(0.55, 0.55, 0.55)
        gradeGlow:SetVertexColor(0.5, 0.5, 0.5)
        gradeGlow:SetAlpha(0.2)
    end
end

local function RefreshUI()
    _refreshPortraitModel()

    if not Umbra_Database then
        _paintProfile(nil)
        for _, row in ipairs(statRows) do row.frame:Hide(); row.iconFrame:Hide() end
        return
    end

    local myName = UnitName("player")
    local myRealm = GetNormalizedRealmName()
    local myKey = myName .. "-" .. myRealm

    local myData = Umbra_Database[myKey]
    if not myData then
        local lk = myKey:lower()
        for k, v in pairs(Umbra_Database) do
            if k:lower() == lk then myData = v; break end
        end
    end

    for _, row in ipairs(statRows) do row.frame:Hide(); row.iconFrame:Hide() end
    _paintProfile(myData)

    if myData then
        local spec = myData.spec or "Unknown"

        -- Render categories in role-appropriate order. Drop any field the
        -- backend didn't export for this player (e.g. healer-only throughput
        -- on a DPS row) rather than filling the slot with zeros.
        local order = STAT_ORDER_FOR_ROLE[myData.role or "dps"] or STAT_ORDER_FOR_ROLE.dps
        local stats = {}
        for _, key in ipairs(order) do
            local v = myData[key]
            if v ~= nil then
                table.insert(stats, { key = key, val = v })
            end
        end

        for i, stat in ipairs(stats) do
            if statRows[i] then
                local row = statRows[i]
                local iconTex = STAT_ICONS[stat.key]
                if stat.key == "dps_ilvl" then
                    iconTex = SPEC_ICONS[myData.spec] or "Interface\\Icons\\INV_Misc_QuestionMark"
                end
                row.icon:SetTexture(iconTex or "Interface\\Icons\\INV_Misc_QuestionMark")

                local labelFmt = STAT_LABELS_MAP[stat.key] or stat.key
                if labelFmt:find("%%s") then
                    labelFmt = string.format(labelFmt, spec)
                end
                row.label:SetText(labelFmt)

                local r, g, b = GetStatColorRGB(stat.val)
                row.bar:SetValue(stat.val)
                row.bar:SetStatusBarColor(r, g, b, 0.45)

                local hex = RGBToHex(r, g, b)
                if stat.key == "timed_pct" then
                    row.value:SetText("|cff" .. hex .. stat.val .. "%|r |cff888888(" .. (myData.runs or 0) .. ")|r")
                else
                    row.value:SetText("|cff" .. hex .. stat.val .. "%|r")
                end
                row.frame:Show()
                row.iconFrame:Show()
            end
        end
    end
end

-- ── Settings (used by Core.lua and UmbraLogger.lua) ────────────────────────
-- Merge defaults into the saved-variables table so we never clobber values
-- set by other modules (e.g., UmbraLogger's autoCombatLog) or by the user
-- across sessions. Direct assignment was destroying both.

UmbraSettings = UmbraSettings or {}
local _defaults = {
    showTooltips = true,
    showLFG = true,
    autoCombatLog = true,
    panelScale = 1.0,
    panelAlpha = 1.0,
    minimapButton = true,
    minimapAngle = 225,  -- Degrees around minimap center (lower-left default).
}
for k, v in pairs(_defaults) do
    if UmbraSettings[k] == nil then
        UmbraSettings[k] = v
    end
end

-- Apply persisted scale/alpha immediately so the frame matches what the
-- user configured last session.
UmbraFrame:SetScale(UmbraSettings.panelScale)
UmbraFrame:SetAlpha(UmbraSettings.panelAlpha)

-- ── Settings Column (right-side panel) ─────────────────────────────────────
-- Always visible alongside the stat breakdown. Save-on-change — no explicit
-- apply/revert buttons, since SavedVariables persist each field immediately.

-- Vertical divider between columns.
local divider = UmbraFrame:CreateTexture(nil, "ARTWORK")
divider:SetColorTexture(0.3, 0.2, 0.45, 0.5)
divider:SetSize(1, FRAME_HEIGHT - 60)
divider:SetPoint("TOPLEFT", UmbraFrame, "TOPLEFT", LEFT_COL_WIDTH, -44)

local settingsPanel = CreateFrame("Frame", nil, UmbraFrame)
settingsPanel:SetPoint("TOPLEFT", UmbraFrame, "TOPLEFT", LEFT_COL_WIDTH + 10, -44)
settingsPanel:SetPoint("BOTTOMRIGHT", UmbraFrame, "BOTTOMRIGHT", -14, 14)

local settingsTitle = settingsPanel:CreateFontString(nil, "OVERLAY")
settingsTitle:SetPoint("TOPLEFT", settingsPanel, "TOPLEFT", 4, -4)
settingsTitle:SetFont("Fonts\\FRIZQT__.TTF", 13, "OUTLINE")
settingsTitle:SetTextColor(0.85, 0.7, 1)
settingsTitle:SetText("SETTINGS")

-- Thin accent line under the section title.
local titleAccent = settingsPanel:CreateTexture(nil, "ARTWORK")
titleAccent:SetColorTexture(0.54, 0.17, 0.89, 0.7)
titleAccent:SetSize(RIGHT_COL_WIDTH - 40, 1)
titleAccent:SetPoint("TOPLEFT", settingsTitle, "BOTTOMLEFT", 0, -4)

local SETTINGS_ROW_WIDTH = RIGHT_COL_WIDTH - 28

-- Checkbox row.
local function CreateCheckRow(parent, yOffset, label, key)
    local row = CreateFrame("Frame", nil, parent)
    row:SetSize(SETTINGS_ROW_WIDTH, 26)
    row:SetPoint("TOPLEFT", parent, "TOPLEFT", 4, yOffset)

    local cb = CreateFrame("CheckButton", nil, row, "UICheckButtonTemplate")
    cb:SetPoint("RIGHT", row, "RIGHT", 0, 0)
    cb:SetSize(24, 24)
    cb:SetChecked(UmbraSettings[key] and true or false)

    local text = row:CreateFontString(nil, "OVERLAY")
    text:SetPoint("LEFT", row, "LEFT", 2, 0)
    text:SetPoint("RIGHT", cb, "LEFT", -4, 0)
    text:SetJustifyH("LEFT")
    text:SetFont("Fonts\\FRIZQT__.TTF", 11, "")
    text:SetTextColor(0.92, 0.92, 0.92)
    text:SetText(label)

    cb:SetScript("OnClick", function(self)
        UmbraSettings[key] = self:GetChecked() and true or false
    end)
    return cb
end

-- Slider row.
local function CreateSliderRow(parent, yOffset, label, key, minV, maxV, step, onChange)
    local row = CreateFrame("Frame", nil, parent)
    row:SetSize(SETTINGS_ROW_WIDTH, 34)
    row:SetPoint("TOPLEFT", parent, "TOPLEFT", 4, yOffset)

    local text = row:CreateFontString(nil, "OVERLAY")
    text:SetPoint("TOPLEFT", row, "TOPLEFT", 2, 0)
    text:SetFont("Fonts\\FRIZQT__.TTF", 11, "")
    text:SetTextColor(0.92, 0.92, 0.92)
    text:SetText(label)

    local valText = row:CreateFontString(nil, "OVERLAY")
    valText:SetPoint("TOPRIGHT", row, "TOPRIGHT", 0, 0)
    valText:SetFont("Fonts\\FRIZQT__.TTF", 11, "")
    valText:SetTextColor(1, 0.85, 0.2)

    local slider = CreateFrame("Slider", nil, row, "OptionsSliderTemplate")
    slider:SetPoint("BOTTOMLEFT", row, "BOTTOMLEFT", 2, 0)
    slider:SetPoint("BOTTOMRIGHT", row, "BOTTOMRIGHT", -2, 0)
    slider:SetMinMaxValues(minV, maxV)
    slider:SetValueStep(step)
    slider:SetObeyStepOnDrag(true)
    slider:SetValue(UmbraSettings[key] or minV)
    if slider.Low then slider.Low:SetText("") end
    if slider.High then slider.High:SetText("") end
    if slider.Text then slider.Text:SetText("") end

    local function updateText(v) valText:SetText(string.format("%.2f", v)) end
    updateText(slider:GetValue())

    slider:SetScript("OnValueChanged", function(self, v)
        UmbraSettings[key] = v
        updateText(v)
        if onChange then onChange(v) end
    end)
    return slider
end

-- Row handles kept so Reset can drive them without a reopen.
local cbTooltips  = CreateCheckRow(settingsPanel, -30, "Tooltip grades on players", "showTooltips")
local cbLFG       = CreateCheckRow(settingsPanel, -60, "LFG applicant grades & tooltips", "showLFG")
local cbAutoLog   = CreateCheckRow(settingsPanel, -90, "Auto /combatlog on M+ start", "autoCombatLog")
local slScale     = CreateSliderRow(settingsPanel, -160, "Panel scale", "panelScale", 0.6, 1.5, 0.05,
    function(v) UmbraFrame:SetScale(v) end)
local slAlpha     = CreateSliderRow(settingsPanel, -210, "Panel alpha", "panelAlpha", 0.4, 1.0, 0.05,
    function(v) UmbraFrame:SetAlpha(v) end)

-- Reset-to-defaults button (drives the live controls so they reflect new values).
local resetBtn = CreateFrame("Button", nil, settingsPanel, "UIPanelButtonTemplate")
resetBtn:SetSize(140, 22)
resetBtn:SetPoint("BOTTOM", settingsPanel, "BOTTOM", 0, 10)
resetBtn:SetText("Reset to defaults")
-- Deferred: onReset() fills in minimap-related resets once those handles
-- exist later in the file. Stored as a table we append closures to so
-- reset can drive widgets declared after this button.
local _resetHandlers = {}
resetBtn:SetScript("OnClick", function()
    for k, v in pairs(_defaults) do UmbraSettings[k] = v end
    UmbraFrame:SetScale(UmbraSettings.panelScale)
    UmbraFrame:SetAlpha(UmbraSettings.panelAlpha)
    cbTooltips:SetChecked(UmbraSettings.showTooltips)
    cbLFG:SetChecked(UmbraSettings.showLFG)
    cbAutoLog:SetChecked(UmbraSettings.autoCombatLog)
    slScale:SetValue(UmbraSettings.panelScale)
    slAlpha:SetValue(UmbraSettings.panelAlpha)
    for _, fn in ipairs(_resetHandlers) do fn() end
end)

-- ── Minimap Button ─────────────────────────────────────────────────────────
-- Self-contained, LibDBIcon-free. Polar positioning around the minimap so
-- shift-drag moves it along the edge at a consistent radius.

local MINIMAP_RADIUS = 80

local minimapBtn = CreateFrame("Button", "UmbraMinimapButton", Minimap)
minimapBtn:SetFrameStrata("MEDIUM")
minimapBtn:SetFrameLevel(8)
minimapBtn:SetSize(32, 32)
minimapBtn:RegisterForClicks("LeftButtonUp", "RightButtonUp")
minimapBtn:RegisterForDrag("LeftButton")
minimapBtn:SetMovable(true)

-- Icon (uses the same spell icon as the header).
local mbIcon = minimapBtn:CreateTexture(nil, "BACKGROUND")
mbIcon:SetSize(20, 20)
mbIcon:SetPoint("CENTER")
mbIcon:SetTexture("Interface\\AddOns\\Umbra\\textures\\logo.tga")
-- Our logo is already round-friendly on a dark backdrop, and applying
-- the portrait alpha mask to it crops the outer glow. Skip both the
-- square-border trim coords and the mask.

-- Ring border.
local mbBorder = minimapBtn:CreateTexture(nil, "OVERLAY")
mbBorder:SetSize(52, 52)
mbBorder:SetPoint("TOPLEFT", 0, 0)
mbBorder:SetTexture("Interface\\Minimap\\MiniMap-TrackingBorder")

local function _applyMinimapPosition()
    local a = math.rad(UmbraSettings.minimapAngle or 225)
    local x = math.cos(a) * MINIMAP_RADIUS
    local y = math.sin(a) * MINIMAP_RADIUS
    minimapBtn:ClearAllPoints()
    minimapBtn:SetPoint("CENTER", Minimap, "CENTER", x, y)
end
_applyMinimapPosition()

-- Shift-drag: update stored angle each frame by computing the mouse position
-- relative to minimap center.
local function _onUpdateDrag(self)
    local mx, my = Minimap:GetCenter()
    local scale = Minimap:GetEffectiveScale()
    local cx, cy = GetCursorPosition()
    cx, cy = cx / scale, cy / scale
    local a = math.deg(math.atan2(cy - my, cx - mx))
    if a < 0 then a = a + 360 end
    UmbraSettings.minimapAngle = a
    _applyMinimapPosition()
end
minimapBtn:SetScript("OnDragStart", function(self)
    self:SetScript("OnUpdate", _onUpdateDrag)
end)
minimapBtn:SetScript("OnDragStop", function(self)
    self:SetScript("OnUpdate", nil)
end)

minimapBtn:SetScript("OnClick", function(self, button)
    if button == "LeftButton" then
        if UmbraFrame:IsShown() then
            UmbraFrame:Hide()
        else
            RefreshUI()
            UmbraFrame:Show()
        end
    end
end)

minimapBtn:SetScript("OnEnter", function(self)
    GameTooltip:SetOwner(self, "ANCHOR_LEFT")
    GameTooltip:AddLine("|cffffffffWoW|r|cff8a2be2Umbra|r|cffffffff.gg|r")
    GameTooltip:AddLine("Left-click: open grades panel", 1, 1, 1)
    GameTooltip:AddLine("Shift-drag: move around minimap", 0.7, 0.7, 0.7)
    GameTooltip:Show()
end)
minimapBtn:SetScript("OnLeave", function() GameTooltip:Hide() end)

-- Honour the saved-variables visibility toggle.
local function _applyMinimapVisibility()
    if UmbraSettings.minimapButton then minimapBtn:Show() else minimapBtn:Hide() end
end
_applyMinimapVisibility()

-- Minimap-button toggle checkbox (placed in the settings column so users
-- can hide it without editing saved variables).
local cbMinimap = CreateCheckRow(settingsPanel, -120, "Minimap button", "minimapButton")
cbMinimap:HookScript("OnClick", _applyMinimapVisibility)

table.insert(_resetHandlers, function()
    cbMinimap:SetChecked(UmbraSettings.minimapButton)
    _applyMinimapPosition()
    _applyMinimapVisibility()
end)

-- ── Slash Command ───────────────────────────────────────────────────────────
-- Unified view: `/umbra` toggles the frame; stats + settings are always both
-- visible in their respective columns.

SLASH_UMBRA1 = "/umbra"
SlashCmdList["UMBRA"] = function()
    if UmbraFrame:IsShown() then
        UmbraFrame:Hide()
    else
        RefreshUI()
        UmbraFrame:Show()
    end
end
