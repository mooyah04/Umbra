-- Umbra.gg Stats Panel
-- Opens with /umbra command

local ADDON_PATH = "Interface\\AddOns\\Umbra\\textures\\"
local FRAME_WIDTH = 360
local FRAME_HEIGHT = 470

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
headerIcon:SetTexture("Interface\\Icons\\spell_shadow_twilight")
headerIcon:SetTexCoord(0.07, 0.93, 0.07, 0.93)

local titleText = UmbraFrame:CreateFontString(nil, "OVERLAY")
titleText:SetPoint("LEFT", headerIcon, "RIGHT", 8, 0)
titleText:SetFont("Fonts\\FRIZQT__.TTF", 16, "OUTLINE")
titleText:SetText("|cff8a2be2Umbra|r|cffffffff.gg|r")

-- ── Grade Section (custom textures) ─────────────────────────────────────────

local gradeAnchor = CreateFrame("Frame", nil, UmbraFrame)
gradeAnchor:SetSize(200, 200)
gradeAnchor:SetPoint("TOP", UmbraFrame, "TOP", 0, -30)

-- Custom glow (soft radial)
local glowTex = gradeAnchor:CreateTexture(nil, "BACKGROUND", nil, 0)
glowTex:SetSize(220, 220)
glowTex:SetPoint("CENTER")
glowTex:SetTexture(ADDON_PATH .. "glow")
glowTex:SetBlendMode("ADD")

-- Custom starburst (animated)
local starTex = gradeAnchor:CreateTexture(nil, "BACKGROUND", nil, 1)
starTex:SetSize(200, 200)
starTex:SetPoint("CENTER")
starTex:SetTexture(ADDON_PATH .. "starburst")
starTex:SetBlendMode("ADD")

-- Custom ring
local ringTex = gradeAnchor:CreateTexture(nil, "ARTWORK", nil, 0)
ringTex:SetSize(160, 160)
ringTex:SetPoint("CENTER")
ringTex:SetTexture(ADDON_PATH .. "ring")
ringTex:SetBlendMode("ADD")

-- Spec text (above grade)
local specText = gradeAnchor:CreateFontString(nil, "OVERLAY")
specText:SetPoint("TOP", gradeAnchor, "TOP", 0, -20)
specText:SetFont("Fonts\\FRIZQT__.TTF", 13, "OUTLINE")
specText:SetTextColor(0.85, 0.85, 0.85)

-- Grade letter
local gradeText = gradeAnchor:CreateFontString(nil, "OVERLAY")
gradeText:SetPoint("CENTER", gradeAnchor, "CENTER", 0, -8)
gradeText:SetFont("Fonts\\FRIZQT__.TTF", 74, "OUTLINE, THICKOUTLINE")
gradeText:SetShadowOffset(3, -3)
gradeText:SetShadowColor(0, 0, 0, 1)

-- Spin animation for starburst
local spinAngle = 0
local spinFrame = CreateFrame("Frame")
spinFrame:SetScript("OnUpdate", function(self, elapsed)
    if not UmbraFrame:IsShown() then return end
    spinAngle = spinAngle + elapsed * 12
    if spinAngle >= 360 then spinAngle = spinAngle - 360 end
    starTex:SetRotation(math.rad(spinAngle))
end)

-- ── Stat Row Builder ────────────────────────────────────────────────────────

local STAT_ICONS = {
    dps_perf = "Interface\\Icons\\ability_warrior_bladestorm",
    dps_ilvl = nil, -- Set dynamically from spec
    throughput = "Interface\\Icons\\spell_holy_flashheal",
    utility = "Interface\\Icons\\spell_frost_chainsofice",
    survivability = "Interface\\Icons\\spell_holy_ashestoashes",
    cd_usage = "Interface\\Icons\\spell_nature_timestop",
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

local STAT_LABELS_MAP = {
    dps_perf = "Overall vs %s",
    dps_ilvl = "iLvl vs %s",
    throughput = "HPS vs %s",
    utility = "Utility/Interrupts",
    survivability = "Survivability",
    cd_usage = "CD Management",
    timed_pct = "Keys Timed",
}

local GRADE_COLORS = {
    ["S+"] = {1, 0.5, 0}, ["S"] = {1, 0.5, 0},
    ["A+"] = {0.64, 0.21, 0.93}, ["A"] = {0.64, 0.21, 0.93}, ["A-"] = {0.64, 0.21, 0.93},
    ["B+"] = {0, 0.44, 0.87}, ["B"] = {0, 0.44, 0.87}, ["B-"] = {0, 0.44, 0.87},
    ["C+"] = {0.12, 1, 0}, ["C"] = {0.12, 1, 0}, ["C-"] = {0.12, 1, 0},
    ["D+"] = {1, 1, 1}, ["D"] = {1, 1, 1}, ["D-"] = {1, 1, 1},
    ["F"] = {0.62, 0.62, 0.62}, ["F-"] = {0.62, 0.62, 0.62},
}

local function GetStatColorRGB(v)
    if v >= 80 then return 0, 0.9, 0
    elseif v >= 60 then return 1, 0.85, 0
    elseif v >= 40 then return 1, 0.45, 0
    else return 0.9, 0, 0
    end
end

local function RGBToHex(r, g, b)
    return string.format("%02x%02x%02x", r * 255, g * 255, b * 255)
end

local ROW_WIDTH = FRAME_WIDTH - 32
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
local rowStartY = -215
for i = 1, 7 do
    statRows[i] = CreateStatRow(UmbraFrame, rowStartY - (i - 1) * (ROW_HEIGHT + 6))
end

-- ── Footer ──────────────────────────────────────────────────────────────────

local dbText = UmbraFrame:CreateFontString(nil, "OVERLAY")
dbText:SetPoint("BOTTOM", UmbraFrame, "BOTTOM", 0, 14)
dbText:SetFont("Fonts\\FRIZQT__.TTF", 11, "")
dbText:SetTextColor(0.4, 0.4, 0.4)

-- ── Refresh ─────────────────────────────────────────────────────────────────

local function RefreshUI()
    if not Umbra_Database then
        gradeText:SetText("--")
        gradeText:SetTextColor(0.4, 0.4, 0.4)
        specText:SetText("No data loaded")
        for _, row in ipairs(statRows) do row.frame:Hide(); row.iconFrame:Hide() end
        dbText:SetText("Tracking 0 players")
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

    if myData then
        local gc = GRADE_COLORS[myData.grade] or {1, 1, 1}
        gradeText:SetText(myData.grade)
        gradeText:SetTextColor(gc[1], gc[2], gc[3])

        -- Tint all glow textures to match grade color
        glowTex:SetVertexColor(gc[1], gc[2], gc[3], 1)
        starTex:SetVertexColor(gc[1], gc[2], gc[3], 0.8)
        ringTex:SetVertexColor(gc[1], gc[2], gc[3], 0.9)

        local role = myData.role or "dps"
        local spec = myData.spec or "Unknown"
        local RI = {
            tank = "|TInterface\\LFGFrame\\UI-LFG-ICON-PORTRAITROLES:16:16:0:0:64:64:0:19:22:41|t",
            healer = "|TInterface\\LFGFrame\\UI-LFG-ICON-PORTRAITROLES:16:16:0:0:64:64:20:39:1:20|t",
            dps = "|TInterface\\LFGFrame\\UI-LFG-ICON-PORTRAITROLES:16:16:0:0:64:64:20:39:22:41|t",
        }
        specText:SetText((RI[role] or "") .. " " .. spec)

        local stats = {}
        if myData.dps_perf then table.insert(stats, { key = "dps_perf", val = myData.dps_perf }) end
        if myData.dps_ilvl then table.insert(stats, { key = "dps_ilvl", val = myData.dps_ilvl }) end
        if myData.throughput then table.insert(stats, { key = "throughput", val = myData.throughput }) end
        if myData.utility then table.insert(stats, { key = "utility", val = myData.utility }) end
        if myData.survivability then table.insert(stats, { key = "survivability", val = myData.survivability }) end
        if myData.cd_usage then table.insert(stats, { key = "cd_usage", val = myData.cd_usage }) end
        if myData.timed_pct then table.insert(stats, { key = "timed_pct", val = myData.timed_pct }) end

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
    else
        gradeText:SetText("N/R")
        gradeText:SetTextColor(0.4, 0.4, 0.4)
        glowTex:SetVertexColor(0.3, 0.3, 0.3, 0.5)
        starTex:SetVertexColor(0.3, 0.3, 0.3, 0.3)
        ringTex:SetVertexColor(0.3, 0.3, 0.3, 0.4)
        specText:SetText("Not Rated")
    end

    local total = 0
    for _ in pairs(Umbra_Database) do total = total + 1 end
    dbText:SetText("Tracking " .. total .. " players")
end

-- ── Slash Command ───────────────────────────────────────────────────────────

SLASH_UMBRA1 = "/umbra"
SlashCmdList["UMBRA"] = function()
    if UmbraFrame:IsShown() then
        UmbraFrame:Hide()
    else
        RefreshUI()
        UmbraFrame:Show()
    end
end

-- ── Settings (used by Core.lua) ─────────────────────────────────────────────

UmbraSettings = {
    showTooltips = true,
    showLFG = true,
}
