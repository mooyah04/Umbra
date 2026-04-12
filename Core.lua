local UMBRA_PURPLE = "|cff8a2be2"
local GREY = "|cffaaaaaa"
local WHITE = "|cffffffff"
local GREEN = "|cff00ff00"
local YELLOW = "|cffffff00"
local ORANGE = "|cffff8000"
local RED = "|cffff0000"
local LIGHT_GREY = "|cff666666"

-- Grade color mapping
local function GetGradeColor(grade)
    if grade == "S+" or grade == "S" then return "|cffff8000"  -- orange (legendary)
    elseif grade == "A+" or grade == "A" or grade == "A-" then return "|cffa335ee"  -- purple (epic)
    elseif grade == "B+" or grade == "B" or grade == "B-" then return "|cff0070dd"  -- blue (rare)
    elseif grade == "C+" or grade == "C" or grade == "C-" then return "|cff1eff00"  -- green (uncommon)
    elseif grade == "D+" or grade == "D" or grade == "D-" then return "|cffffffff"  -- white (common)
    else return "|cff9d9d9d"  -- grey (poor)
    end
end

-- Color a stat value based on score (0-100)
local function GetStatColor(value)
    if value >= 80 then return GREEN
    elseif value >= 60 then return YELLOW
    elseif value >= 40 then return ORANGE
    else return RED
    end
end

-- Role display names
local ROLE_NAMES = {
    tank = "Tank",
    healer = "Healer",
    dps = "DPS",
}

-- Role icons (using built-in WoW role icons)
local ROLE_ICONS = {
    tank = "|TInterface\\LFGFrame\\UI-LFG-ICON-PORTRAITROLES:14:14:0:0:64:64:0:19:22:41|t",
    healer = "|TInterface\\LFGFrame\\UI-LFG-ICON-PORTRAITROLES:14:14:0:0:64:64:20:39:1:20|t",
    dps = "|TInterface\\LFGFrame\\UI-LFG-ICON-PORTRAITROLES:14:14:0:0:64:64:20:39:22:41|t",
}

-- Stat labels per role
local STAT_LABELS = {
    tank = {
        { key = "dps_perf", label = "DPS (vs Spec)" },
        { key = "utility", label = "Utility/Kicks" },
        { key = "survivability", label = "Survivability" },
    },
    healer = {
        { key = "throughput", label = "HPS (vs Spec)" },
        { key = "dps_perf", label = "Healer DPS" },
        { key = "utility", label = "Utility/Dispels" },
        { key = "survivability", label = "Survivability" },
    },
    dps = {
        { key = "dps_perf", label = "DPS (vs Spec)" },
        { key = "utility", label = "Utility/Kicks" },
        { key = "survivability", label = "Survivability" },
    },
}

local function AddUmbraTooltip(self, data)
    self:AddLine(" ")
    self:AddLine(UMBRA_PURPLE .. "Umbra.io|r")

    -- Grade + Role line
    local gradeColor = GetGradeColor(data.grade)
    local role = data.role or "dps"
    local roleIcon = ROLE_ICONS[role] or ""
    local roleName = ROLE_NAMES[role] or "DPS"

    self:AddDoubleLine(
        roleIcon .. " " .. GREY .. roleName .. "|r",
        gradeColor .. data.grade .. "|r"
    )

    -- Category stats
    local stats = STAT_LABELS[role] or STAT_LABELS["dps"]
    for _, stat in ipairs(stats) do
        local value = data[stat.key]
        if value and value > 0 then
            local color = GetStatColor(value)
            self:AddDoubleLine(
                GREY .. stat.label .. ":|r",
                color .. value .. "%|r"
            )
        end
    end

    -- Key completion rate
    if data.timed_pct then
        local color = GetStatColor(data.timed_pct)
        self:AddDoubleLine(
            GREY .. "Keys Timed:|r",
            color .. data.timed_pct .. "%|r" .. GREY .. " (" .. (data.runs or 0) .. " runs)|r"
        )
    end
end

-- Tooltip hook
local function OnTooltipSetUnit(self)
    local _, unit = self:GetUnit()
    if not unit or not UnitIsPlayer(unit) then return end

    local name, realm = UnitFullName(unit)
    if not name then return end

    -- Same-realm players return nil/empty realm, so fall back to our own realm
    if not realm or realm == "" then
        realm = GetNormalizedRealmName()
    end

    local fullName = name .. "-" .. realm:gsub("%s+", "")

    -- Case-insensitive lookup since WoW may return names in different cases
    local data = nil
    if Umbra_Database then
        -- Try exact match first
        data = Umbra_Database[fullName]
        -- Fall back to case-insensitive search
        if not data then
            local lowerKey = fullName:lower()
            for key, value in pairs(Umbra_Database) do
                if key:lower() == lowerKey then
                    data = value
                    break
                end
            end
        end
    end

    if data then
        AddUmbraTooltip(self, data)
    end
end

-- Hook into GameTooltip
TooltipDataProcessor.AddTooltipPostCall(Enum.TooltipDataType.Unit, function(tooltip)
    if tooltip == GameTooltip then
        OnTooltipSetUnit(tooltip)
    end
end)
