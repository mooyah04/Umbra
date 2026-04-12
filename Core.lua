local UMBRA_PURPLE = "|cff8a2be2"
local GREY = "|cffaaaaaa"
local WHITE = "|cffffffff"
local GREEN = "|cff00ff00"
local YELLOW = "|cffffff00"
local ORANGE = "|cffff8000"
local RED = "|cffff0000"

-- ── Utility Functions ───────────────────────────────────────────────────────

local function GetGradeColor(grade)
    if grade == "S+" or grade == "S" then return "|cffff8000"  -- orange (legendary)
    elseif grade == "A+" or grade == "A" or grade == "A-" then return "|cffa335ee"  -- purple (epic)
    elseif grade == "B+" or grade == "B" or grade == "B-" then return "|cff0070dd"  -- blue (rare)
    elseif grade == "C+" or grade == "C" or grade == "C-" then return "|cff1eff00"  -- green (uncommon)
    elseif grade == "D+" or grade == "D" or grade == "D-" then return "|cffffffff"  -- white (common)
    else return "|cff9d9d9d"  -- grey (poor)
    end
end

local function GetStatColor(value)
    if value >= 80 then return GREEN
    elseif value >= 60 then return YELLOW
    elseif value >= 40 then return ORANGE
    else return RED
    end
end

local ROLE_NAMES = {
    tank = "Tank",
    healer = "Healer",
    dps = "DPS",
}

local ROLE_ICONS = {
    tank = "|TInterface\\LFGFrame\\UI-LFG-ICON-PORTRAITROLES:14:14:0:0:64:64:0:19:22:41|t",
    healer = "|TInterface\\LFGFrame\\UI-LFG-ICON-PORTRAITROLES:14:14:0:0:64:64:20:39:1:20|t",
    dps = "|TInterface\\LFGFrame\\UI-LFG-ICON-PORTRAITROLES:14:14:0:0:64:64:20:39:22:41|t",
}

-- Stat labels are built dynamically using the player's spec name
local function GetStatLabels(role, spec)
    spec = spec or "Spec"
    if role == "tank" then
        return {
            { key = "dps_perf", label = "Overall vs " .. spec },
            { key = "dps_ilvl", label = "iLvl vs " .. spec },
            { key = "utility", label = "Utility/Kicks" },
            { key = "survivability", label = "Survivability" },
            { key = "cd_usage", label = "Cooldown Usage" },
        }
    elseif role == "healer" then
        return {
            { key = "throughput", label = "HPS vs " .. spec },
            { key = "dps_perf", label = "Healer DPS" },
            { key = "dps_ilvl", label = "iLvl vs " .. spec },
            { key = "utility", label = "Utility/Dispels" },
            { key = "survivability", label = "Survivability" },
            { key = "cd_usage", label = "Cooldown Usage" },
        }
    else
        return {
            { key = "dps_perf", label = "Overall vs " .. spec },
            { key = "dps_ilvl", label = "iLvl vs " .. spec },
            { key = "utility", label = "Utility/Kicks" },
            { key = "survivability", label = "Survivability" },
            { key = "cd_usage", label = "Cooldown Usage" },
        }
    end
end

-- ── Database Lookup ─────────────────────────────────────────────────────────

local function LookupPlayer(fullName)
    if not Umbra_Database then return nil end

    -- Try exact match first
    local data = Umbra_Database[fullName]
    if data then return data end

    -- Fall back to case-insensitive search
    local lowerKey = fullName:lower()
    for key, value in pairs(Umbra_Database) do
        if key:lower() == lowerKey then
            return value
        end
    end
    return nil
end

local function GetFullName(name, realm)
    if not realm or realm == "" then
        realm = GetNormalizedRealmName()
    end
    return name .. "-" .. realm:gsub("%s+", "")
end

-- ── Tooltip Rendering ───────────────────────────────────────────────────────

local function AddUmbraTooltip(tooltip, data)
    tooltip:AddLine(" ")
    tooltip:AddLine(UMBRA_PURPLE .. "Umbra.gg|r")

    local gradeColor = GetGradeColor(data.grade)
    local role = data.role or "dps"
    local roleIcon = ROLE_ICONS[role] or ""
    local roleName = ROLE_NAMES[role] or "DPS"

    -- Spec/role on left, grade on right (same line)
    tooltip:AddDoubleLine(
        roleIcon .. " " .. GREY .. (data.spec or roleName) .. "|r",
        gradeColor .. data.grade .. "|r"
    )
    -- Make the grade side larger
    local numLines = tooltip:NumLines()
    local gradeRight = _G["GameTooltipTextRight" .. numLines]
    if gradeRight then
        gradeRight:SetFont("Fonts\\FRIZQT__.TTF", 20, "OUTLINE, THICKOUTLINE")
    end

    local spec = data.spec or "Spec"
    local stats = GetStatLabels(role, spec)
    for _, stat in ipairs(stats) do
        local value = data[stat.key]
        if value then
            local color = GetStatColor(value)
            tooltip:AddDoubleLine(
                GREY .. stat.label .. ":|r",
                color .. value .. "%|r"
            )
        end
    end

    if data.timed_pct then
        local color = GetStatColor(data.timed_pct)
        tooltip:AddDoubleLine(
            GREY .. "Keys Timed:|r",
            color .. data.timed_pct .. "%|r" .. GREY .. " (" .. (data.runs or 0) .. " runs)|r"
        )
    end
end

-- Compact grade string for inline display (e.g., on LFG applicant rows)
local function GetGradeString(data)
    if not data then return nil end
    local gradeColor = GetGradeColor(data.grade)
    return gradeColor .. data.grade .. "|r"
end

-- ── Tooltip Hook (hover over players in world) ─────────────────────────────

local function OnTooltipSetUnit(self)
    local _, unit = self:GetUnit()
    if not unit or not UnitIsPlayer(unit) then return end

    local name, realm = UnitFullName(unit)
    if not name then return end

    local fullName = GetFullName(name, realm)
    local data = LookupPlayer(fullName)

    if data then
        AddUmbraTooltip(self, data)
    end
end

TooltipDataProcessor.AddTooltipPostCall(Enum.TooltipDataType.Unit, function(tooltip)
    if tooltip == GameTooltip then
        if UmbraSettings and not UmbraSettings.showTooltips then return end
        OnTooltipSetUnit(tooltip)
    end
end)

-- ── LFG Applicant Tooltip (hover over applicants in Group Finder) ───────────

local function OnLFGApplicantEnter(self)
    if not self.applicantID or not self.memberIdx then return end

    local name, class, localizedClass, level, itemLevel, honorLevel,
          tank, healer, damage, assignedRole, relationship, dungeonScore,
          pvpItemLevel = C_LFGList.GetApplicantMemberInfo(self.applicantID, self.memberIdx)

    if not name then return end

    -- Name comes as "Player-Realm" from the API
    local data = LookupPlayer(name)

    if data then
        AddUmbraTooltip(GameTooltip, data)
        GameTooltip:Show()
    end
end

-- Hook the applicant member tooltips in the Application Viewer
local function HookApplicationViewer()
    local appViewer = LFGListFrame and LFGListFrame.ApplicationViewer
    if not appViewer then return end

    -- Hook into the scroll box that contains applicant entries
    local scrollBox = appViewer.ScrollBox
    if not scrollBox then return end

    -- When new frames are created in the scroll box, hook their OnEnter
    scrollBox:RegisterCallback("OnDataRangeChanged", function()
        scrollBox:ForEachFrame(function(button)
            if button and button.Members then
                for _, member in pairs(button.Members) do
                    if member and not member._umbraHooked then
                        member:HookScript("OnEnter", OnLFGApplicantEnter)
                        member._umbraHooked = true
                    end
                end
            end
        end)
    end)
end

-- ── LFG Search Results (browsing groups to join) ────────────────────────────

local function OnLFGSearchResultEnter(self)
    if not self.resultID then return end

    local searchResultInfo = C_LFGList.GetSearchResultInfo(self.resultID)
    if not searchResultInfo then return end

    -- Get the group leader's name
    local leaderName = searchResultInfo.leaderName
    if not leaderName then return end

    local data = LookupPlayer(leaderName)

    if data then
        AddUmbraTooltip(GameTooltip, data)
        GameTooltip:Show()
    end
end

local function HookSearchPanel()
    local searchPanel = LFGListFrame and LFGListFrame.SearchPanel
    if not searchPanel then return end

    local scrollBox = searchPanel.ScrollBox
    if not scrollBox then return end

    scrollBox:RegisterCallback("OnDataRangeChanged", function()
        scrollBox:ForEachFrame(function(button)
            if button and not button._umbraHooked then
                button:HookScript("OnEnter", OnLFGSearchResultEnter)
                button._umbraHooked = true
            end
        end)
    end)
end

-- ── Applicant Grade Column (inline grade next to applicant names) ───────────

local function UpdateApplicantGrades()
    local appViewer = LFGListFrame and LFGListFrame.ApplicationViewer
    if not appViewer then return end

    local scrollBox = appViewer.ScrollBox
    if not scrollBox then return end

    scrollBox:ForEachFrame(function(button)
        if not button or not button.applicantID then return end

        local numMembers = C_LFGList.GetNumApplicantMembers(button.applicantID)
        if not numMembers then return end

        for i = 1, numMembers do
            local member = button.Members and button.Members[i]
            if member then
                local name = C_LFGList.GetApplicantMemberInfo(button.applicantID, i)
                if name then
                    local data = LookupPlayer(name)
                    if data then
                        -- Add grade text next to the member's name
                        if not member.UmbraGrade then
                            member.UmbraGrade = member:CreateFontString(nil, "OVERLAY", "GameFontNormalSmall")
                            member.UmbraGrade:SetPoint("RIGHT", member, "RIGHT", -5, 0)
                        end
                        local gradeColor = GetGradeColor(data.grade)
                        member.UmbraGrade:SetText(gradeColor .. data.grade .. "|r")
                        member.UmbraGrade:Show()
                    elseif member.UmbraGrade then
                        member.UmbraGrade:Hide()
                    end
                end
            end
        end
    end)
end

-- ── Initialize Hooks ────────────────────────────────────────────────────────

local loader = CreateFrame("Frame")
loader:RegisterEvent("ADDON_LOADED")
loader:SetScript("OnEvent", function(self, event, addonName)
    if addonName == "Blizzard_GroupFinder" or addonName == "Blizzard_LFGList" then
        -- Group finder loaded, hook into it
        C_Timer.After(0.1, function()
            HookApplicationViewer()
            HookSearchPanel()
        end)
    end
end)

-- Also try hooking immediately in case the group finder is already loaded
if LFGListFrame then
    HookApplicationViewer()
    HookSearchPanel()
end

-- Update grade display when applicant list changes
if LFGListFrame and LFGListFrame.ApplicationViewer then
    hooksecurefunc(LFGListFrame.ApplicationViewer, "UpdateResults", UpdateApplicantGrades)
end

-- Fallback: hook UpdateResults when the frame becomes available
loader:RegisterEvent("PLAYER_ENTERING_WORLD")
loader:SetScript("OnEvent", function(self, event, addonName)
    if event == "ADDON_LOADED" and (addonName == "Blizzard_GroupFinder" or addonName == "Blizzard_LFGList") then
        C_Timer.After(0.1, function()
            HookApplicationViewer()
            HookSearchPanel()
            if LFGListFrame and LFGListFrame.ApplicationViewer then
                hooksecurefunc(LFGListFrame.ApplicationViewer, "UpdateResults", UpdateApplicantGrades)
            end
        end)
    elseif event == "PLAYER_ENTERING_WORLD" then
        -- Try hooking on login in case group finder is already loaded
        if LFGListFrame then
            HookApplicationViewer()
            HookSearchPanel()
            if LFGListFrame.ApplicationViewer then
                hooksecurefunc(LFGListFrame.ApplicationViewer, "UpdateResults", UpdateApplicantGrades)
            end
        end
        self:UnregisterEvent("PLAYER_ENTERING_WORLD")
    end
end)
