# GraphQL queries for Warcraft Logs API v2

# Fetch a character's recent M+ reports
CHARACTER_RECENT_REPORTS = """
query($name: String!, $serverSlug: String!, $serverRegion: String!, $limit: Int!) {
  characterData {
    character(name: $name, serverSlug: $serverSlug, serverRegion: $serverRegion) {
      id
      name
      classID
      server { slug region { slug } }
      recentReports(limit: $limit) {
        data {
          code
          title
          startTime
          endTime
          zone { id name }
        }
      }
    }
  }
}
"""

# Fetch M+ fights from a report
REPORT_FIGHTS = """
query($code: String!) {
  reportData {
    report(code: $code) {
      fights(difficulty: 10) {
        id
        encounterID
        name
        keystoneLevel
        keystoneTime
        startTime
        endTime
        kill
      }
    }
  }
}
"""

# Fetch player performance data for specific fights in a report
REPORT_PLAYER_DATA = """
query($code: String!, $fightIDs: [Int!]!) {
  reportData {
    report(code: $code) {
      playerDetails(fightIDs: $fightIDs)
      damageTable: table(fightIDs: $fightIDs, dataType: DamageDone)
      healingTable: table(fightIDs: $fightIDs, dataType: Healing)
      damageTakenTable: table(fightIDs: $fightIDs, dataType: DamageTaken)
      interruptTable: table(fightIDs: $fightIDs, dataType: Interrupts)
      dispelTable: table(fightIDs: $fightIDs, dataType: Dispels)
      deathTable: table(fightIDs: $fightIDs, dataType: Deaths)
      castsTable: table(fightIDs: $fightIDs, dataType: Casts)
    }
  }
}
"""

# Fetch buffs for a specific player (by sourceID) in a fight
REPORT_PLAYER_BUFFS = """
query($code: String!, $fightIDs: [Int!]!, $sourceID: Int!) {
  reportData {
    report(code: $code) {
      buffsTable: table(fightIDs: $fightIDs, dataType: Buffs, sourceID: $sourceID)
    }
  }
}
"""
