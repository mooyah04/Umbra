import SearchBar from "@/components/SearchBar";

export default function Home() {
  return (
    <div className="min-h-screen pt-32 pb-24 px-6 md:px-12 max-w-7xl mx-auto">
      {/* Hero Search Section */}
      <section className="flex flex-col items-center justify-center text-center mb-20">
        <h2 className="font-[family-name:var(--font-headline)] font-extrabold text-5xl md:text-7xl lg:text-8xl tracking-tighter mb-8 text-on-surface">
          LOOK UP <span className="text-primary italic">ANY PLAYER.</span>
        </h2>
        <SearchBar />
        <p className="mt-6 font-[family-name:var(--font-label)] text-xs uppercase tracking-[0.2em] text-on-surface-variant">
          Indexed: <span className="text-primary">12.4M</span> Characters
          {" • "}
          <span className="text-secondary">482</span> Realms
          {" • "}
          <span className="text-tertiary">Real-time</span> Log Parsing
        </p>
      </section>

      {/* Bento Layout */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
        {/* Trending Players */}
        <div className="md:col-span-8 bg-surface-container-high rounded-xl overflow-hidden relative">
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-primary via-transparent to-transparent" />
          <div className="p-8">
            <div className="flex justify-between items-end mb-8">
              <div>
                <h3 className="font-[family-name:var(--font-headline)] font-bold text-2xl uppercase tracking-tighter">
                  Trending Players
                </h3>
                <p className="font-[family-name:var(--font-label)] text-xs text-on-surface-variant uppercase tracking-widest mt-1">
                  High-Frequency Activity (Last 60m)
                </p>
              </div>
              <span className="font-[family-name:var(--font-label)] text-[10px] text-primary bg-primary-container/20 px-2 py-1 rounded">
                LIVE UPDATES
              </span>
            </div>
            <div className="space-y-1">
              <TrendingRow
                name="Zyr-Area52"
                region="US"
                spec="Havoc Demon Hunter"
                ilvl={489}
                stat="148.2k DPS"
                statColor="text-primary"
                rank="Global Rank #12"
                icon="swords"
                iconColor="text-primary"
                iconBg="bg-primary"
                bgClass="bg-surface-container"
              />
              <TrendingRow
                name="Lumina-TwistingNether"
                region="EU"
                spec="Holy Paladin"
                ilvl={491}
                stat="112.5k HPS"
                statColor="text-tertiary"
                rank="Top 0.1% Healer"
                icon="ecg_heart"
                iconColor="text-tertiary"
                iconBg="bg-tertiary"
                bgClass="bg-surface-container-low"
              />
              <TrendingRow
                name="Korg-TarrenMill"
                region="EU"
                spec="Blood Death Knight"
                ilvl={488}
                stat="3.4k Rating"
                statColor="text-on-surface"
                rank="Mythic+ Elite"
                icon="shield"
                iconColor="text-secondary"
                iconBg="bg-secondary"
                bgClass="bg-surface-container"
              />
            </div>
          </div>
        </div>

        {/* Right sidebar */}
        <div className="md:col-span-4 flex flex-col gap-6">
          {/* Recent History */}
          <div className="bg-surface-container-low p-8 rounded-xl flex-grow">
            <h3 className="font-[family-name:var(--font-headline)] font-bold text-xl uppercase tracking-tighter mb-6 flex items-center gap-2">
              <span className="material-symbols-outlined text-sm">history</span>
              History
            </h3>
            <ul className="space-y-4">
              <HistoryItem name="Vantuss-Kazzak" time="Updated 2m ago" />
              <HistoryItem name="Nex-Stormrage" time="Updated 14m ago" />
              <HistoryItem name="Echo-Ragnaros" time="Updated 1h ago" />
            </ul>
            <button className="w-full mt-8 py-3 bg-surface-container-highest hover:bg-surface-bright transition-all font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest text-on-surface-variant rounded">
              Clear Recent History
            </button>
          </div>

          {/* CTA Block */}
          <div className="bg-gradient-to-br from-primary-container to-surface-container-highest p-8 rounded-xl relative overflow-hidden">
            <div className="relative z-10">
              <h4 className="font-[family-name:var(--font-headline)] font-black text-2xl leading-none text-on-primary-container italic">
                RAID PREP
                <br />
                MODE
              </h4>
              <p className="font-[family-name:var(--font-body)] text-xs text-on-primary-container/80 mt-2 mb-4">
                Analyze your entire roster&apos;s performance in one click.
              </p>
              <button className="bg-primary text-on-primary font-[family-name:var(--font-label)] text-[10px] px-4 py-2 uppercase tracking-widest font-bold rounded">
                Explore Tools
              </button>
            </div>
            <span className="material-symbols-outlined absolute -bottom-4 -right-4 text-9xl text-primary opacity-5">
              query_stats
            </span>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="mt-20 border-t border-outline-variant/10 pt-8 flex flex-col md:flex-row justify-between items-center gap-6">
        <div className="flex items-center gap-8">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-primary shadow-[0_0_8px_#8a2be2]" />
            <span className="font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest text-on-surface-variant">
              Global Sync: Stable
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-xs text-on-surface-variant">dns</span>
            <span className="font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest text-on-surface-variant">
              Latency: 24ms
            </span>
          </div>
        </div>
        <div className="font-[family-name:var(--font-label)] text-[10px] text-on-surface-variant uppercase tracking-[0.3em]">
          WoWUmbra.gg © 2025 • Deep-Audit Performance Data
        </div>
      </footer>
    </div>
  );
}

function TrendingRow({
  name,
  region,
  spec,
  ilvl,
  stat,
  statColor,
  rank,
  icon,
  iconColor,
  iconBg,
  bgClass,
}: {
  name: string;
  region: string;
  spec: string;
  ilvl: number;
  stat: string;
  statColor: string;
  rank: string;
  icon: string;
  iconColor: string;
  iconBg: string;
  bgClass: string;
}) {
  const regionColor = region === "US" ? "bg-secondary/10 text-secondary border-secondary/20" : "bg-primary/10 text-primary border-primary/20";
  return (
    <div className={`group flex items-center justify-between p-4 ${bgClass} hover:bg-surface-container-highest transition-all cursor-pointer`}>
      <div className="flex items-center gap-4">
        <div className="w-12 h-12 bg-surface-container-lowest flex items-center justify-center relative overflow-hidden rounded">
          <div className={`absolute inset-0 opacity-20 ${iconBg}`} />
          <span className={`material-symbols-outlined ${iconColor}`}>{icon}</span>
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="font-[family-name:var(--font-headline)] font-bold text-lg">{name}</span>
            <span className={`text-[10px] font-[family-name:var(--font-label)] px-1 border uppercase ${regionColor}`}>
              {region}
            </span>
          </div>
          <p className="font-[family-name:var(--font-label)] text-xs text-on-surface-variant">
            {spec} • ILVL {ilvl}
          </p>
        </div>
      </div>
      <div className="text-right">
        <span className={`font-[family-name:var(--font-label)] text-sm ${statColor}`}>{stat}</span>
        <p className="text-[10px] font-[family-name:var(--font-label)] text-on-surface-variant uppercase tracking-widest">
          {rank}
        </p>
      </div>
    </div>
  );
}

function HistoryItem({ name, time }: { name: string; time: string }) {
  return (
    <li className="flex items-center justify-between group cursor-pointer">
      <div className="flex flex-col">
        <span className="font-[family-name:var(--font-body)] font-medium text-on-surface group-hover:text-primary transition-colors">
          {name}
        </span>
        <span className="font-[family-name:var(--font-label)] text-[10px] text-on-surface-variant uppercase">
          {time}
        </span>
      </div>
      <span className="material-symbols-outlined text-on-surface-variant opacity-0 group-hover:opacity-100 transition-opacity">
        arrow_forward_ios
      </span>
    </li>
  );
}
