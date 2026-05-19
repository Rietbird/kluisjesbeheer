// Conciërge-handleiding, in-app. Tekstueel, geen screenshots, geen echte namen.
// De IT-/installatiehandleiding blijft een los document (docs/).

function Stap({ children }) {
  return <li className="mb-1.5">{children}</li>
}

function Sectie({ id, titel, children }) {
  return (
    <section id={id} className="scroll-mt-20 mb-10">
      <h2 className="text-xl font-bold text-navy dark:text-white mb-3 pt-2">{titel}</h2>
      <div className="text-sm text-slate-700 dark:text-slate-300 space-y-3 leading-relaxed">
        {children}
      </div>
    </section>
  )
}

function Tip({ children }) {
  return (
    <div className="border-l-3 border-primary bg-primary-50/60 dark:bg-slate-800 rounded-r-lg px-4 py-2.5 my-3">
      <div className="text-xs font-semibold uppercase tracking-wide text-primary mb-1">Goed om te weten</div>
      <div className="text-sm text-slate-600 dark:text-slate-300">{children}</div>
    </div>
  )
}

const SECTIES = [
  ['start', 'Inloggen & overzicht'],
  ['kleuren', 'Kleuren & status'],
  ['toewijzen', 'Een kluisje toewijzen'],
  ['defect', 'Een defect melden'],
  ['reserve', 'Reservesleutel'],
  ['innemen', 'Een huur beëindigen'],
  ['ruilen', 'Kluisjes ruilen'],
  ['clusters', 'Kluisjes indelen in clusters'],
  ['zoeken', 'Zoeken & filteren'],
  ['rapport', 'Rapporten'],
]

export default function Handleiding({ onClose }) {
  return (
    <div className="max-w-5xl mx-auto px-5 py-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-navy dark:text-white">Handleiding</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">Dagelijks gebruik voor conciërges</p>
        </div>
        <button onClick={onClose}
          className="text-sm text-slate-500 dark:text-slate-400 hover:text-primary border border-slate-300 dark:border-slate-600 rounded-lg px-4 py-2 transition-colors">
          ← Terug
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-[200px_1fr] gap-8">
        {/* Inhoudsopgave */}
        <nav className="hidden md:block sticky top-6 self-start text-sm space-y-1">
          {SECTIES.map(([id, titel]) => (
            <a key={id} href={`#${id}`}
              className="block text-slate-500 dark:text-slate-400 hover:text-primary border-l-2 border-transparent hover:border-primary pl-3 py-1 transition-colors">
              {titel}
            </a>
          ))}
        </nav>

        {/* Inhoud */}
        <div>
          <Sectie id="start" titel="Inloggen & overzicht">
            <p>De applicatie werkt in de browser. U logt in met uw schoolaccount (hetzelfde Microsoft-account als voor e-mail) — er zijn geen aparte wachtwoorden.</p>
            <p>Na het inloggen ziet u uw vestiging(en). Bij meerdere vestigingen kiest u er één via de tabbladen bovenaan. Het hoofdscherm toont alle kluisjes als tegels met het kluisnummer en — afhankelijk van de status — de huurder of een label.</p>
          </Sectie>

          <Sectie id="kleuren" titel="Kleuren & status">
            <p>De kleur van een tegel vertelt in één oogopslag wat er met het kluisje aan de hand is:</p>
            <ul className="list-disc pl-5 space-y-1">
              <li><strong>Groen — Vrij.</strong> Beschikbaar voor toewijzing.</li>
              <li><strong>Blauw — Uitgeleend.</strong> Toont de naam van de huidige huurder.</li>
              <li><strong>Oranje — Uitgeleend, borg niet betaald.</strong> Met een 💰-teken.</li>
              <li><strong>Amber — Defect (en vrij).</strong> Gemarkeerd als defect, geen huurder.</li>
              <li><strong>Blauw met amber rand — Defect én in gebruik.</strong> ⚠ voor het nummer; de huurder blijft zichtbaar.</li>
              <li><strong>Rood — Vrij, maar sleutel/borg openstaand</strong> van de vorige huurder (🔑 / 💰).</li>
            </ul>
            <p>Een 🔑 bij een huurder betekent dat er een reservesleutel is uitgegeven.</p>
          </Sectie>

          <Sectie id="toewijzen" titel="Een kluisje toewijzen">
            <ol className="list-decimal pl-5">
              <Stap><strong>Open een vrij kluisje</strong> (groene tegel).</Stap>
              <Stap><strong>Klik op "Toewijzen".</strong></Stap>
              <Stap><strong>Zoek de leerling</strong> op naam of stamnummer.</Stap>
              <Stap><strong>Vul periode en borg in</strong> (van/tot-datum, eventueel borgbedrag en of het betaald is).</Stap>
              <Stap><strong>Bevestig.</strong> Het kluisje wordt blauw en toont de naam.</Stap>
            </ol>
            <Tip>Een leerling kan maar één kluisje per vestiging hebben. Een kluisje kan pas opnieuw worden toegewezen als de sleutel is ingeleverd én de borg is teruggestort.</Tip>
          </Sectie>

          <Sectie id="defect" titel="Een defect melden">
            <p>Een kluisje kan defect zijn terwijl het nog in gebruik is. Het defect markeren raakt de huurder en de opmerkingen <strong>niet</strong> aan.</p>
            <ol className="list-decimal pl-5">
              <Stap><strong>Open het kluisje</strong> — vrij of verhuurd, beide kan.</Stap>
              <Stap><strong>Klik op "Markeer als defect".</strong> Er verschijnt een amber "defect"-label.</Stap>
              <Stap>In het overzicht krijgt een verhuurd-en-defect kluisje een amber rand met ⚠; de huurder blijft zichtbaar.</Stap>
              <Stap><strong>Opgelost?</strong> Open het kluisje en klik op "Defect opheffen".</Stap>
            </ol>
            <Tip>Een defect kluisje kan niet aan een nieuwe leerling worden toegewezen — hef eerst het defect op. Een lopende verhuur blijft wél gewoon doorlopen.</Tip>
          </Sectie>

          <Sectie id="reserve" titel="Reservesleutel">
            <p>Bij een verhuurd kluisje kunt u vastleggen dat er een reservesleutel is afgegeven.</p>
            <ol className="list-decimal pl-5">
              <Stap>Open het verhuurde kluisje.</Stap>
              <Stap>Vink <strong>"Reservesleutel uitgegeven"</strong> aan in het huurderblok.</Stap>
              <Stap>Kies de datum van afgifte.</Stap>
            </ol>
            <p>In het overzicht verschijnt een 🔑 bij de huurder. Een eventueel borgbedrag voor de reservesleutel noteert u in het opmerkingenveld.</p>
          </Sectie>

          <Sectie id="innemen" titel="Een huur beëindigen">
            <ol className="list-decimal pl-5">
              <Stap><strong>Open het verhuurde kluisje</strong> en klik op "Huur beëindigen".</Stap>
              <Stap><strong>Vink aan</strong> of de sleutel is ingeleverd en of de borg is teruggestort.</Stap>
              <Stap><strong>Bevestig.</strong> Het kluisje wordt weer vrij.</Stap>
            </ol>
            <p>Is de sleutel niet ingeleverd of de borg niet teruggestort, dan blijft het kluisje rood gemarkeerd met een waarschuwing, en kan het niet opnieuw worden toegewezen totdat dit is afgehandeld. Vanuit het detailscherm kunt u dit later alsnog op "afgehandeld" zetten.</p>
          </Sectie>

          <Sectie id="ruilen" titel="Kluisjes ruilen">
            <p>Soms krijgt een leerling een kluisje dat fysiek te hoog of te laag zit en wil die ruilen met een andere leerling. Beide leerlingen wisselen van kluisje in één handeling — zonder huren te beëindigen en opnieuw toe te wijzen.</p>
            <ol className="list-decimal pl-5">
              <Stap>Open het verhuurde kluisje van de ene leerling.</Stap>
              <Stap>Klik onderaan op <strong>"Ruilen met…"</strong>.</Stap>
              <Stap>Zoek het kluisje van de andere leerling (kluisnummer, naam of stamnummer).</Stap>
              <Stap>Controleer de bevestigingsregel (<em>leerling A (kluis X) ↔ leerling B (kluis Y)</em>) en klik <strong>"Ruil bevestigen"</strong>.</Stap>
            </ol>
            <Tip>Alleen het kluisnummer wisselt. Periode, borg, sleutelstatus, reservesleutel en opmerkingen blijven per leerling ongewijzigd. De leerlingen ruilen onderling ook fysiek de sleutels. Ruilen kan alleen tussen twee verhuurde kluisjes binnen dezelfde vestiging.</Tip>
          </Sectie>

          <Sectie id="clusters" titel="Kluisjes indelen in clusters">
            <p>Een vestiging kan meerdere <strong>clusters</strong> hebben (bijv. per verdieping of gang). Na een import staan kluisjes meestal in "Standaard". U kunt ze herindelen op drie manieren.</p>

            <p className="font-semibold text-navy dark:text-white mt-4">Een reeks verplaatsen</p>
            <ol className="list-decimal pl-5">
              <Stap>Ga naar <strong>Beheer → Vestigingen</strong>, maak het doelcluster aan en selecteer het.</Stap>
              <Stap>Bij "Bestaande kluisjes naar dit cluster halen": kies de <strong>prefix</strong> uit de lijst en vul <strong>van</strong> en <strong>tot</strong> in.</Stap>
              <Stap>Klik <strong>"Verplaats reeks naar dit cluster"</strong>.</Stap>
            </ol>
            <Tip>De prefix kiest u uit een lijst — niets typen. Voorloopnullen maken niet uit (1 vindt ook nummer 0001). U kunt meerdere reeksen achter elkaar doen; de prefix blijft staan.</Tip>

            <p className="font-semibold text-navy dark:text-white mt-4">Een selectie verplaatsen</p>
            <ol className="list-decimal pl-5">
              <Stap>Selecteer het doelcluster, klik op "Selecteer voor verwijderen" (ook de selectie-modus voor verplaatsen) en vink kluisjes aan.</Stap>
              <Stap>Klik <strong>"Verplaats naar dit cluster"</strong>.</Stap>
            </ol>

            <p className="font-semibold text-navy dark:text-white mt-4">Eén los kluisje (vanuit het overzicht)</p>
            <ol className="list-decimal pl-5">
              <Stap>Open het kluisje in het overzicht.</Stap>
              <Stap>Klik op <strong>"Verplaats naar cluster"</strong>, kies het doelcluster en bevestig.</Stap>
            </ol>
            <p>Verplaatsen verandert alleen de indeling — huurder, borg, sleutel en opmerkingen blijven ongewijzigd. Alleen binnen dezelfde vestiging.</p>
          </Sectie>

          <Sectie id="zoeken" titel="Zoeken & filteren">
            <p>Bovenaan vindt u een zoekbalk en filters:</p>
            <ul className="list-disc pl-5 space-y-1">
              <li><strong>Zoeken</strong> op kluisnummer, sleutelnummer, leerlingnaam of stamnummer.</li>
              <li><strong>Filter</strong> op status: Alles, Vrij, Uitgeleend, Defect, of openstaande sleutel/borg.</li>
              <li><strong>Cluster</strong> — beperk tot een gang of afdeling binnen de vestiging.</li>
            </ul>
            <p>Na een aanpassing blijft het detailscherm open staan, zodat u meerdere handelingen op hetzelfde kluisje kunt doen zonder uw plek in de lijst kwijt te raken.</p>
          </Sectie>

          <Sectie id="rapport" titel="Rapporten">
            <p>Via de werkbalk maakt u PDF-overzichten, per vestiging of klas:</p>
            <ul className="list-disc pl-5 space-y-1">
              <li><strong>Openstaande sleutels</strong> — wie heeft nog niet ingeleverd.</li>
              <li><strong>Openstaande borg</strong> — niet betaald of niet teruggestort.</li>
              <li><strong>Actieve toewijzingen</strong> en <strong>innameoverzicht</strong> — handig aan het eind van het schooljaar.</li>
              <li><strong>Defecte kluisjes</strong> — overzicht voor de technische dienst.</li>
            </ul>
          </Sectie>

          <p className="text-xs text-slate-400 dark:text-slate-500 pt-6 border-t border-slate-200 dark:border-slate-700">
            Kluisjesbeheer · Handleiding voor conciërges
          </p>
        </div>
      </div>
    </div>
  )
}
