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

# Fetch M+ fights from a report.
#
# `friendlyPlayers` + `masterData.actors` are included so ingest can filter
# out fights where the target player didn't participate BEFORE paying for
# the much-more-expensive REPORT_PLAYER_DATA call (playerDetails + four
# tables). A player appearing in ~5 of ~50 fights across their recent
# reports used to cost ~50 playerDetails queries; with this filter it's
# ~5. Adding these fields to the existing round-trip is nearly free.
REPORT_FIGHTS = """
query($code: String!) {
  reportData {
    report(code: $code) {
      startTime
      masterData {
        actors(type: "Player") { id name }
      }
      fights(difficulty: 10) {
        id
        encounterID
        name
        keystoneLevel
        keystoneTime
        keystoneBonus
        startTime
        endTime
        kill
        rating
        averageItemLevel
        keystoneAffixes
        friendlyPlayers
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
      healingReceivedTable: table(fightIDs: $fightIDs, dataType: Healing, hostilityType: Friendlies)
    }
  }
}
"""

# Fetch buffs and debuffs for a specific player (by sourceID) in a fight
REPORT_PLAYER_AURAS = """
query($code: String!, $fightIDs: [Int!]!, $sourceID: Int!) {
  reportData {
    report(code: $code) {
      buffsTable: table(fightIDs: $fightIDs, dataType: Buffs, sourceID: $sourceID)
      debuffsOnEnemies: table(fightIDs: $fightIDs, dataType: Debuffs, hostilityType: Enemies, sourceID: $sourceID)
    }
  }
}
"""
