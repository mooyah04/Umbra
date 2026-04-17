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
    elseif grade == "D+" or grade == "D" or grade == "D-" then return "|cffffcc00"  -- amber (caution)
    else return "|cffff3030"  -- red (failing)
    end
end

local function GetStatColor(value)
    if value >= 80 then return GREEN
    elseif value >= 60 then return YELLOW
    elseif value >= 40 then return ORANGE
    else return RED
    end
end

-- Stat labels = exactly the categories that feed the composite grade.
-- Keep in sync with backend ROLE_WEIGHTS + lua_writer ROLE_EXPORT_FIELDS.
-- Display-only fields (dps_ilvl, timed_pct) aren't shown here because
-- they don't contribute to the grade, and the tooltip is tight on space.
local function GetStatLabels(role, spec)
    spec = spec or "Spec"
    if role == "tank" then
        return {
            { key = "dps_perf", label = "Damage vs " .. spec },
            { key = "utility", label = "Utility/Kicks" },
            { key = "survivability", label = "Survivability" },
            { key = "cd_usage", label = "Cooldown Usage" },
            { key = "cpm", label = "Casts/min" },
        }
    elseif role == "healer" then
        return {
            { key = "throughput", label = "Healing vs " .. spec },
            { key = "dps_perf", label = "Healer DPS" },
            { key = "utility", label = "Utility/Dispels" },
            { key = "survivability", label = "Survivability" },
            { key = "cd_usage", label = "Cooldown Usage" },
            { key = "cpm", label = "Casts/min" },
        }
    else
        return {
            { key = "dps_perf", label = "Damage vs " .. spec },
            { key = "utility", label = "Utility/Kicks" },
            { key = "survivability", label = "Survivability" },
            { key = "cd_usage", label = "Cooldown Usage" },
            { key = "cpm", label = "Casts/min" },
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
--
-- We previously called SetFont on GameTooltipTextRight<N> to render the
-- grade in a big outlined font. WoW recycles those text regions across
-- every tooltip and font changes persist on the region object — so even
-- with OnHide cleanup, hover-to-hover transitions (where OnHide doesn't
-- fire) leaked our font onto Raider.IO and other addons' text.
--
-- Render the grade in normal size with bold color formatting instead.
-- No shared state mutation, no leaks. We can revisit a fancy display
-- later using a custom FontString we own — but that's a bigger refactor.

local function AddUmbraTooltip(tooltip, data)
    tooltip:AddLine(" ")

    local gradeColor = GetGradeColor(data.grade)
    local role = data.role or "dps"

    -- "Umbra.gg" header on the left, grade on the right. Native WoW
    -- tooltip already shows "<spec> <class>" above us, so no need to
    -- duplicate role/spec text here. Grade color alone carries the
    -- visual emphasis — no SetFont so this is safe for tooltip line
    -- recycling (previously ran into text-region font leaks onto other
    -- addons' tooltips when we used SetFont).
    tooltip:AddDoubleLine(
        UMBRA_PURPLE .. "Umbra.gg|r",
        gradeColor .. data.grade .. "|r"
    )

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

end

-- Compact grade string for inline display (e.g., on LFG applicant rows)
local function GetGradeString(data)
    if not data then return nil end
    local gradeColor = GetGradeColor(data.grade)
    return gradeColor .. data.grade .. "|r"
end

-- ── Tooltip Hook (hover over players in world) ─────────────────────────────
-- The TooltipDataHandler sometimes invokes our post-call with a tooltip
-- whose unit reference is tainted or nil (SetWorldCursor path, e.g. when
-- the cursor sweeps across nameplates/world objects). Calling
-- UnitIsPlayer or UnitFullName directly on that reference raises a
-- "Secret values are only allowed during untainted execution" error —
-- fatal noise that can fire 100+ times a minute. We use
-- TooltipUtil.GetDisplayedUnit when available (sanctioned, taint-safe)
-- and pcall every unit API so any lingering taint quietly bails instead
-- of bubbling to BugSack.

local function _getTooltipUnit(tooltip)
    if TooltipUtil and TooltipUtil.GetDisplayedUnit then
        local okU, _, unit = pcall(TooltipUtil.GetDisplayedUnit, tooltip)
        if okU and unit then return unit end
    end
    local okG, _, unit = pcall(tooltip.GetUnit, tooltip)
    if okG then return unit end
    return nil
end

local function OnTooltipSetUnit(tooltip)
    local unit = _getTooltipUnit(tooltip)
    if not unit then return end

    local okPlayer, isPlayer = pcall(UnitIsPlayer, unit)
    if not okPlayer or not isPlayer then return end

    local okName, name, realm = pcall(UnitFullName, unit)
    if not okName or not name then return end

    local fullName = GetFullName(name, realm)
    local data = LookupPlayer(fullName)

    if data then
        AddUmbraTooltip(tooltip, data)
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
    print("|cff8a2be2[Umbra]|r OnEnter fired")
    if UmbraSettings and not UmbraSettings.showLFG then
        print("|cff8a2be2[Umbra]|r showLFG disabled, bail")
        return
    end

    -- Blizzard puts applicantID on the parent button and uses the frame's
    -- own GetID() as memberIdx. Reading them off `self` directly (as we
    -- used to) returned nil on every hover.
    local parent = self:GetParent()
    local applicantID = parent and parent.applicantID
    local memberIdx = self:GetID()
    print(string.format("|cff8a2be2[Umbra]|r applicantID=%s memberIdx=%s",
        tostring(applicantID), tostring(memberIdx)))
    if not applicantID or not memberIdx or memberIdx == 0 then return end

    local name = C_LFGList.GetApplicantMemberInfo(applicantID, memberIdx)
    print(string.format("|cff8a2be2[Umbra]|r name=%s", tostring(name)))
    if not name then return end

    -- Name comes as "Player-Realm" from the API
    local data = LookupPlayer(name)
    print(string.format("|cff8a2be2[Umbra]|r lookup=%s", data and ("FOUND " .. (data.grade or "?")) or "NIL"))

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
    if UmbraSettings and not UmbraSettings.showLFG then return end
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
--
-- Raider.IO occupies the RIGHT edge of each applicant row with its M+
-- score. If RIO is installed we yield that real estate to it and rely
-- on our tooltip-on-hover instead — no info lost, no visual conflict.

local function HasRaiderIO()
    if C_AddOns and C_AddOns.IsAddOnLoaded then
        return C_AddOns.IsAddOnLoaded("RaiderIO")
    end
    if IsAddOnLoaded then
        return IsAddOnLoaded("RaiderIO")
    end
    return false
end

-- Ensure every currently-visible applicant member frame has our OnEnter
-- attached. Called from the UpdateResults hook below. We used to rely on
-- scrollBox:RegisterCallback("OnDataRangeChanged", ...) for this, but that
-- doesn't fire for the initial render — so hooks never attached and the
-- tooltip silently did nothing.
--
-- Kept separate from UpdateApplicantGrades on purpose: badges bail out
-- when Raider.IO is installed (to avoid pixel-fighting for the same
-- spot), but the tooltip should still enrich regardless — RIO and Umbra
-- happily coexist in the tooltip body.
local function AttachApplicantHoverHooks()
    local appViewer = LFGListFrame and LFGListFrame.ApplicationViewer
    local scrollBox = appViewer and appViewer.ScrollBox
    if not scrollBox then
        print("|cff8a2be2[Umbra]|r AttachHover: no scrollBox")
        return
    end
    local buttons, members = 0, 0
    scrollBox:ForEachFrame(function(button)
        buttons = buttons + 1
        if button and button.Members then
            for _, member in pairs(button.Members) do
                members = members + 1
                if member and not member._umbraHooked then
                    member:HookScript("OnEnter", OnLFGApplicantEnter)
                    member._umbraHooked = true
                end
            end
        end
    end)
    print(string.format("|cff8a2be2[Umbra]|r AttachHover: buttons=%d members=%d", buttons, members))
end

local function UpdateApplicantGrades()
    if UmbraSettings and not UmbraSettings.showLFG then
        -- Hide any badges we previously rendered.
        local appViewer = LFGListFrame and LFGListFrame.ApplicationViewer
        local scrollBox = appViewer and appViewer.ScrollBox
        if scrollBox then
            scrollBox:ForEachFrame(function(button)
                if button and button.Members then
                    for _, m in pairs(button.Members) do
                        if m.UmbraGrade then m.UmbraGrade:Hide() end
                    end
                end
            end)
        end
        return
    end
    if HasRaiderIO() then
        -- Don't fight Raider.IO for the same pixels.
        return
    end

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

-- Safe hook: hooksecurefunc raises if the named method doesn't exist on
-- the target table. Blizzard periodically renames/removes internals on
-- the LFG frame (the ScrollBox rework being the most recent), so we
-- verify the method is actually a function before attaching. Tracked
-- per-instance so we never double-hook after ADDON_LOADED + PEW both fire.
local _applicantUpdateResultsHooked = false
local function TryHookApplicantUpdateResults()
    if _applicantUpdateResultsHooked then return end
    local viewer = LFGListFrame and LFGListFrame.ApplicationViewer
    if viewer and type(viewer.UpdateResults) == "function" then
        hooksecurefunc(viewer, "UpdateResults", UpdateApplicantGrades)
        hooksecurefunc(viewer, "UpdateResults", AttachApplicantHoverHooks)
        _applicantUpdateResultsHooked = true
    end
end

-- Update grade display when applicant list changes
TryHookApplicantUpdateResults()

-- Fallback: hook UpdateResults when the frame becomes available
loader:RegisterEvent("PLAYER_ENTERING_WORLD")
loader:SetScript("OnEvent", function(self, event, addonName)
    if event == "ADDON_LOADED" and (addonName == "Blizzard_GroupFinder" or addonName == "Blizzard_LFGList") then
        C_Timer.After(0.1, function()
            HookApplicationViewer()
            HookSearchPanel()
            TryHookApplicantUpdateResults()
        end)
    elseif event == "PLAYER_ENTERING_WORLD" then
        -- Try hooking on login in case group finder is already loaded
        if LFGListFrame then
            HookApplicationViewer()
            HookSearchPanel()
            TryHookApplicantUpdateResults()
        end
        self:UnregisterEvent("PLAYER_ENTERING_WORLD")
    end
end)
