/**
 * @file kb-pages.data.ts
 * @path src/app/admin/intranet/knowledge-base/data/kb-pages.data.ts
 * @project JS web-platform
 * @author JS
 * @created 2026
 * @description STATIC content of the whole internal manual (Knowledge Base). Editing the
 * manual = editing this array in code - see kb-content.ts for the architecture.
 *
 * @editing-guide How to add a new manual page:
 * 1) Add a new object to the `KB_PAGES` array below; `id` must be a unique kebab-case slug.
 *    Beware of collisions across modules (e.g. web / core / shop each have their own
 *    "dashboard" and "logs" route) - hence these pages are prefixed (`web-dashboard`,
 *    `core-dashboard`, `shop-dashboard`, `web-business-logs`, `core-logs`, `shop-logs`).
 * 2) `navGroup` / `navOrder` decide where the page shows in the side menu - no change of
 *    knowledge-base.component.html is needed, the menu is generated from this array
 *    (see KnowledgeBaseComponent.buildNavGroups()).
 * 3) When the page documents a function bound to a specific permission / role, describe it in
 *    `devNote` (visible only in code, NOT translated) - the permission keys match the values
 *    `data: { permission: '...' }` of admin-routing.module.ts 1:1.
 * 4) Images (KBImageBlock.path) belong to `src/assets/kb/<page-id>/...`.
 * 5) ALL user-visible texts (navLabel, header, block content) MUST have both `cz` and `en`
 *    filled in - see `LocalizedText` in kb-content.ts. `devNote` stays in one language
 *    (dev-only, never rendered).
 *
 * @note `support-form` and `news` are NOT in this array - both stay own components / routes
 * (real logic, not static text) - see admin-routing.module.ts.
 */

import { KBPage } from "../../../../shared/interfaces/kb-content";

export const KB_PAGES: KBPage[] = [

  // ── General ──────────────────────────────────────────────────────────────

  {
    id: 'introductions',
    navGroup: 'general',
    navLabel: { cz: 'Introductions', en: 'Introductions' },
    navOrder: 1,
    header: { cz: 'Vítejte u zrodu RPSoftware', en: 'Welcome to the Birth of RPSoftware' },
  sections: [ { blocks: [ { type: 'lead', content: {
      cz: 'Testovací obsah - sem patří úvod',
      en: 'Placeholder content - this is placeholder for intro'
    } } ] } ]
  },
  {
    id: 'security',
    navGroup: 'general',
    navLabel: { cz: 'Přístup', en: 'Access' },
    navOrder: 2,
    header: { cz: 'Přístupové údaje a bezpečnost', en: 'Access Credentials and Security' },
    devNote: 'Popisuje obecná bezpečnostní pravidla (2FA, hesla) - viz PersonalInfoComponent a User::FORCED_2FA_ROLE_NAMES pro skutečnou implementaci vynucení.',
    sections: [ { blocks: [ { type: 'lead', content: {
      cz: 'Testovací obsah - sem patří vysvětlení přihlašování, 2FA a politiky hesel.',
      en: 'Placeholder content - this should explain login, 2FA, and password policy.'
    } } ] } ]
  },
  {
    id: 'contacts',
    navGroup: 'general',
    navLabel: { cz: 'Kontakty', en: 'Contacts' },
    navOrder: 3,
    header: { cz: 'Kontakty na tým', en: 'Team Contacts' },
    sections: [ { blocks: [ { type: 'lead', content: {
      cz: 'Testovací obsah - sem patří seznam kontaktů na klíčové lidi v týmu.',
      en: 'Placeholder content - this should list contacts for key people on the team.'
    } } ] } ]
  },

  // ── Roles ────────────────────────────────────────────────────────────────

  // ── Web (matches the 'web/*' routes of admin-routing.module.ts) ─────────────

  {
    id: 'web-dashboard',
    navGroup: 'web',
    navLabel: { cz: 'Dashboard', en: 'Dashboard' },
    navOrder: 5,
    header: { cz: 'Web - Dashboard', en: 'Web - Dashboard' },
    devNote: "DashboardComponent (web-pages), route 'web/dashboard', permission 'web-view-dashboard'.",
    sections: [ { blocks: [ { type: 'lead', content: {
      cz: 'Testovací obsah - přehledová stránka webového modulu administrace.',
      en: 'Placeholder content - the overview page of the Web admin module.'
    } } ] } ]
  },
  {
    id: 'user-request',
    navGroup: 'web',
    navLabel: { cz: 'Webový formulář', en: 'Web Form' },
    navOrder: 6,
    header: { cz: 'Webový formulář (poptávky)', en: 'Web Form (Inquiries)' },
    devNote: "UserRequestComponent, route 'web/user-request', permission 'web-user-requests-view' (edit/delete vyžadují navíc -update/-delete).",
    sections: [ { blocks: [ { type: 'lead', content: {
      cz: 'Testovací obsah - správa poptávek odeslaných z veřejného webového formuláře.',
      en: 'Placeholder content - management of inquiries submitted via the public web form.'
    } } ] } ]
  },
  {
    id: 'web-business-logs',
    navGroup: 'web',
    navLabel: { cz: 'Business logy', en: 'Business Logs' },
    navOrder: 7,
    header: { cz: 'Web - Business logy', en: 'Web - Business Logs' },
    devNote: "BusinessLogsComponent, route 'web/business-logs', permission 'web-view-web-logs'.",
    sections: [ { blocks: [ { type: 'lead', content: {
      cz: 'Testovací obsah - auditní log akcí provedených ve webovém modulu.',
      en: 'Placeholder content - an audit log of actions performed in the Web module.'
    } } ] } ]
  },
  {
    id: 'sales-leads',
    navGroup: 'web',
    navLabel: { cz: 'Obchodní leady', en: 'Sales Leads' },
    navOrder: 8,
    header: { cz: 'Obchodní leady', en: 'Sales Leads' },
    devNote: "SalesLeadsComponent, route 'web/sales-leads', permission 'web-sales-leads-view'.",
    sections: [ { blocks: [ { type: 'lead', content: {
      cz: 'Testovací obsah - evidence a generování odkazů pro obchodní leady.',
      en: 'Placeholder content - tracking and link generation for sales leads.'
    } } ] } ]
  },
  {
    id: 'edit-news',
    navGroup: 'web',
    navLabel: { cz: 'Novinky (web)', en: 'News (Website)' },
    navOrder: 9,
    header: { cz: 'Správa novinek na webu', en: 'Website News Management' },
    devNote: "EditNewsComponent, route 'web/edit-news', permission 'web-news-view'. Nezaměňovat s KB sekcí 'Novinky' (interní ChangeLog) - tohle je editace novinek zobrazovaných na veřejném webu.",
    sections: [ { blocks: [ { type: 'lead', content: {
      cz: 'Testovací obsah - editace novinek zobrazovaných na veřejném webu.',
      en: 'Placeholder content - editing news items shown on the public website.'
    } } ] } ]
  },
  {
    id: 'edit-website',
    navGroup: 'web',
    navLabel: { cz: 'Editace webu', en: 'Website Editing' },
    navOrder: 10,
    header: { cz: 'Editace obsahu webu', en: 'Website Content Editing' },
    devNote: "EditWebsiteComponent, route 'web/edit-website', permission 'web-edit-website-view'.",
    sections: [ { blocks: [ { type: 'lead', content: {
      cz: 'Testovací obsah - editace obsahových částí veřejného webu.',
      en: 'Placeholder content - editing content sections of the public website.'
    } } ] } ]
  },
  {
    id: 'sales-orders',
    navGroup: 'web',
    navLabel: { cz: 'Přijaté objednávky', en: 'Received Orders' },
    navOrder: 11,
    header: { cz: 'Přijaté objednávky (realizace)', en: 'Received Orders (Fulfillment)' },
    devNote: "SalesOrdersComponent, route 'web/sales-orders', permission 'web-sales-orders-view'. Řádková akce 'Projekt' zakládá navazující záznam v Projects.",
    sections: [ { blocks: [ { type: 'lead', content: {
      cz: 'Testovací obsah - přehled přijatých objednávek/realizací a jejich zpracování.',
      en: 'Placeholder content - overview of received orders/fulfillments and their processing.'
    } } ] } ]
  },
  {
    id: 'support-tickets',
    navGroup: 'web',
    navLabel: { cz: 'Helpdesk tickety', en: 'Helpdesk Tickets' },
    navOrder: 12,
    header: { cz: 'Helpdesk tickety', en: 'Helpdesk Tickets' },
    devNote: "SupportTicketsComponent, route 'web/support-tickets', permission 'web-support-tickets-view'.",
    sections: [ { blocks: [ { type: 'lead', content: {
      cz: 'Testovací obsah - správa helpdesk ticketů přijatých od uživatelů.',
      en: 'Placeholder content - management of helpdesk tickets received from users.'
    } } ] } ]
  },
  {
    id: 'job-applications',
    navGroup: 'web',
    navLabel: { cz: 'Pracovní nabídky', en: 'Job Applications' },
    navOrder: 13,
    header: { cz: 'Pracovní formulář (uchazeči)', en: 'Job Application Form (Candidates)' },
    devNote: "JobApplicationsComponent, route 'web/job-applications', permission 'web-job-applications-view'.",
    sections: [ { blocks: [ { type: 'lead', content: {
      cz: 'Testovací obsah - přehled odeslaných žádostí z pracovního formuláře.',
      en: 'Placeholder content - overview of applications submitted via the job form.'
    } } ] } ]
  },
  {
    id: 'projects',
    navGroup: 'web',
    navLabel: { cz: 'Projekty', en: 'Projects' },
    navOrder: 14,
    header: { cz: 'Projekty a zákaznická vlákna', en: 'Projects and Customer Threads' },
    devNote: "ProjectsComponent, route 'web/projects', permission 'web-projects-view'. Obsahuje i cross-project tabulku zákaznických vláken (web/project-threads).",
    sections: [ { blocks: [ { type: 'lead', content: {
      cz: 'Testovací obsah - správa zákaznických projektů, checkpointů a komunikace.',
      en: 'Placeholder content - management of customer projects, checkpoints, and communication.'
    } } ] } ]
  },

  // ── Core (matches the 'core/*' routes of admin-routing.module.ts) ────────────

  {
    id: 'core-dashboard',
    navGroup: 'core',
    navLabel: { cz: 'Dashboard', en: 'Dashboard' },
    navOrder: 15,
    header: { cz: 'Core - Dashboard', en: 'Core - Dashboard' },
    devNote: "CoreDashboardComponent, route 'core/dashboard', permission 'view-core'.",
    sections: [ { blocks: [ { type: 'lead', content: {
      cz: 'Testovací obsah - přehledová stránka systémového (core) modulu.',
      en: 'Placeholder content - the overview page of the Core (system) module.'
    } } ] } ]
  },
  {
    id: 'welcome-page',
    navGroup: 'core',
    navLabel: { cz: 'Uvítací stránka', en: 'Welcome Page' },
    navOrder: 16,
    header: { cz: 'Uvítací stránka', en: 'Welcome Page' },
    devNote: "WelcomePageComponent, route 'core/welcome-page' (výchozí route pod core/), permission 'core-view-welcome-page'.",
    sections: [ { blocks: [ { type: 'lead', content: {
      cz: 'Testovací obsah - úvodní stránka po přihlášení do administrace.',
      en: 'Placeholder content - the landing page shown after logging into the administration.'
    } } ] } ]
  },
  {
    id: 'edit-legal',
    navGroup: 'core',
    navLabel: { cz: 'Právní dokumenty', en: 'Legal Documents' },
    navOrder: 17,
    header: { cz: 'Editace právních dokumentů (GDPR, TOS...)', en: 'Editing Legal Documents (GDPR, TOS...)' },
    devNote: "EditLegalComponent, route 'core/edit-legal', permission 'core-legal-documents-view|core-legal-config-view'. Vícejazyčný obsah, typy dokumentů se načítají dynamicky z legal/document-types.",
    sections: [ { blocks: [ { type: 'lead', content: {
      cz: 'Testovací obsah - editace vícejazyčného obsahu právních dokumentů (GDPR, obchodní podmínky, cookies).',
      en: 'Placeholder content - editing multilingual content of legal documents (GDPR, terms of service, cookies).'
    } } ] } ]
  },
  {
    id: 'personal-info',
    navGroup: 'core',
    navLabel: { cz: 'Osobní údaje', en: 'Personal Information' },
    navOrder: 18,
    header: { cz: 'Osobní údaje a zabezpečení účtu', en: 'Personal Information and Account Security' },
    devNote: "PersonalInfoComponent, route 'core/personal-info', no permission (every signed-in user; also via the own e-mail in the header). Self-service 2FA toggle a změna hesla.",
    sections: [ { blocks: [ { type: 'lead', content: {
      cz: 'Testovací obsah - správa vlastního profilu, hesla a dvoufaktorového ověření.',
      en: 'Placeholder content - managing your own profile, password, and two-factor authentication.'
    } } ] } ]
  },
  {
    id: 'web-settings',
    navGroup: 'core',
    navLabel: { cz: 'Nastavení webu', en: 'Website Settings' },
    navOrder: 19,
    header: { cz: 'Globální nastavení webu', en: 'Global Website Settings' },
    devNote: "WebSettingsComponent, route 'core/web-settings', permission 'core-legal-config-view'. Firemní údaje, logo, sociální sítě.",
    sections: [ { blocks: [ { type: 'lead', content: {
      cz: 'Testovací obsah - firemní údaje, logo a sociální sítě zobrazované na webu.',
      en: 'Placeholder content - company details, logo, and social media shown on the website.'
    } } ] } ]
  },
  {
    id: 'external-links',
    navGroup: 'core',
    navLabel: { cz: 'Externí odkazy', en: 'External Links' },
    navOrder: 20,
    header: { cz: 'Externí odkazy (rychlé odkazy adminu)', en: 'External Links (Admin Quick Links)' },
    devNote: "ExternalLinksComponent + CoreExternalLinkController, route 'core/external-links', permission 'core-external-links-view' (create/update/delete zvlášť). Odkazy jsou SOUKROMÉ per-uživatel (scoped na user_id na backendu).",
    sections: [ { blocks: [ { type: 'lead', content: {
      cz: 'Testovací obsah - osobní seznam rychlých odkazů na externí nástroje, viditelný jen tobě.',
      en: 'Placeholder content - a personal list of quick links to external tools, visible only to you.'
    } } ] } ]
  },
  {
    id: 'edit-roles',
    navGroup: 'core',
    navLabel: { cz: 'Role a oprávnění', en: 'Roles and Permissions' },
    navOrder: 21,
    header: { cz: 'Správa rolí a oprávnění', en: 'Roles and Permissions Management' },
    devNote: "EditRolesComponent, route 'core/edit-roles'. Přístup NEZÁVISLE na permission systému natvrdo omezen na roli 'sysadmin' (sysadminGuard) - nemá klasický permission klíč.",
    sections: [ { blocks: [ { type: 'lead', content: {
      cz: 'Testovací obsah - správa rolí a jejich oprávnění. Přístupné výhradně sysadminovi.',
      en: 'Placeholder content - management of roles and their permissions. Accessible exclusively to the sysadmin.'
    } } ] } ]
  },
{
    id: 'administrators',
    navGroup: 'core',
    navLabel: { cz: 'Administrátoři', en: 'Administrators' },
    navOrder: 22,
    header: { cz: 'Správa uživatelských účtů', en: 'User Account Management' },
    devNote: "AdministratorsComponent, route 'core/administrators', permission 'core-administrators-view'. Akce: vytvoření 'core-administrators-create'; úprava, změna hesla a znovuodeslání aktivace 'core-administrators-update'; smazání a trvalé smazání z koše 'core-administrators-delete'; koš 'view-deleted'; reporty 'core-administrators-view'; e-mailové domény jen role sysadmin (bez permission klíče, viz isSysadmin). Text popisuje i navazující veřejné stránky: LoginComponent (2FA krok, zapomenuté heslo), ResetPasswordComponent, ActivateAccountComponent - při změně jejich chování aktualizuj kapitoly 05, 08 a 11. Názvy tlačítek jsou v textu záměrně POPISNÉ (ne doslovné), texty aktivační/reset stránky jsou v admin překladech (sekce reset-password / activate-account), anglické popisky v uvozovkách zůstávají jen v e-mailech. Limit hesla 8-16 znaků vychází z password-policy konstant - při změně politiky uprav kapitoly 05 a 11.",
    sections: [

      // ── Introduction ────────────────────────────────────────────────────────────
      {
        blocks: [
          { type: 'lead', content: {
            cz: 'Na této stránce spravujete účty všech lidí, kteří se přihlašují do administrace: zakládáte nové účty, přidělujete role a oprávnění, řešíte hesla, dvoufázové ověření, blokace i mazání. Tento návod vás provede každou funkcí krok za krokem - od založení účtu až po jeho trvalé odstranění.',
            en: 'On this page you manage the accounts of everyone who signs in to the administration: you create new accounts, assign roles and permissions, and handle passwords, two-factor authentication, blocking, and deletion. This guide walks you through every function step by step - from creating an account to removing it permanently.'
          } },
          { type: 'alert', variant: 'info', content: {
            cz: 'Nejdůležitější pravidlo: heslo nového účtu nikdy nezadává ani nezná administrátor. Účet se zakládá bez hesla a uživatel si ho nastaví sám přes odkaz v aktivačním e-mailu.',
            en: 'The most important rule: an administrator never enters or knows the password of a new account. The account is created without a password and the user sets it personally through the link in the activation e-mail.'
          } }
        ]
      },

      // ── 01 ──────────────────────────────────────────────────────────────
      {
        heading: { cz: '01. Kdo stránku vidí a co na ní smí', en: '01. Who Can See the Page and What They Can Do' },
        blocks: [
          { type: 'text', content: {
            cz: 'Co na stránce uvidíte, záleží na vašich oprávněních. Tlačítka a položky, ke kterým oprávnění nemáte, se vůbec nezobrazí - nejde o chybu. Pokud vám některá funkce z tohoto návodu chybí, požádejte o doplnění oprávnění administrátora, který spravuje váš účet.',
            en: 'What you see on the page depends on your permissions. Buttons and menu items you have no permission for are not displayed at all - this is not an error. If a function described in this guide is missing for you, ask the administrator who manages your account to add the permission.'
          } },
          { type: 'grid', cards: [
            { title: { cz: 'Zobrazení stránky', en: 'Viewing the page' }, text: {
              cz: 'Oprávnění core-administrators-view. Vidíte tabulku účtů, detail účtu, filtry, export dat a reporty.',
              en: 'Permission core-administrators-view. You see the accounts table, account details, filters, data export, and reports.'
            } },
            { title: { cz: 'Zakládání účtů', en: 'Creating accounts' }, text: {
              cz: 'Oprávnění core-administrators-create. V nabídce akcí přibude položka pro vytvoření nového záznamu.',
              en: 'Permission core-administrators-create. The action menu gains the item for creating a new record.'
            } },
            { title: { cz: 'Úpravy účtů', en: 'Editing accounts' }, text: {
              cz: 'Oprávnění core-administrators-update. V řádku účtu přibudou akce pro úpravu, změnu hesla a opětovné odeslání aktivace.',
              en: 'Permission core-administrators-update. Each account row gains the actions for editing, changing the password, and resending the activation.'
            } },
            { title: { cz: 'Mazání účtů', en: 'Deleting accounts' }, text: {
              cz: 'Oprávnění core-administrators-delete. V řádku účtu přibude akce pro smazání a v koši možnost trvalého smazání.',
              en: 'Permission core-administrators-delete. Each account row gains the delete action and the trash gains the option to delete permanently.'
            } },
            { title: { cz: 'Koš', en: 'Trash' }, text: {
              cz: 'Oprávnění view-deleted. V nabídce akcí přibude přepnutí mezi aktivními účty a košem.',
              en: 'Permission view-deleted. The action menu gains the switch between active accounts and the trash.'
            } },
            { title: { cz: 'Role sysadmin', en: 'The sysadmin role' }, text: {
              cz: 'Jen sysadmin vidí nastavení povolených e-mailových domén, smí vynutit dvoufázové ověření u konkrétního účtu a smí pracovat s účty, které mají roli sysadmin.',
              en: 'Only a sysadmin sees the allowed e-mail domain settings, may force two-factor authentication on a specific account, and may work with accounts that have the sysadmin role.'
            } }
          ] }
        ]
      },

      // ── 02 ──────────────────────────────────────────────────────────────
      {
        heading: { cz: '02. Orientace na stránce', en: '02. Finding Your Way Around the Page' },
        blocks: [
          { type: 'grid', cards: [
            { title: { cz: 'Nabídka akcí', en: 'Action menu' }, text: {
              cz: 'Rozbalovací nabídka nad tabulkou. Obsahuje zobrazení a skrytí filtrů, vytvoření záznamu, export dat, e-mailové domény (jen sysadmin), reporty a přepnutí mezi aktivními účty a košem.',
              en: 'A drop-down menu above the table. It contains showing and hiding the filters, creating a record, data export, e-mail domains (sysadmin only), reports, and the switch between active accounts and the trash.'
            } },
            { title: { cz: 'Tabulka účtů', en: 'Accounts table' }, text: {
              cz: 'Každý řádek je jeden účet. Sloupce: ID, jméno, e-mail, role, zda je účet blokovaný a datum posledního přihlášení.',
              en: 'Each row is one account. Columns: ID, name, e-mail, role, whether the account is blocked, and the date of the last sign-in.'
            } },
            { title: { cz: 'Akce v řádku', en: 'Row actions' }, text: {
              cz: 'Ikony na konci řádku: lupa (detail), úprava, klíč (změna hesla), obálka (opětovné odeslání aktivace - jen u neaktivovaných účtů) a smazání.',
              en: 'Icons at the end of the row: magnifier (details), edit, key (password change), envelope (resend activation - only for accounts not yet activated), and delete.'
            } },
            { title: { cz: 'Panel filtrů', en: 'Filter panel' }, text: {
              cz: 'Boční panel, který se otevírá z nabídky akcí. Slouží k hledání a řazení účtů - viz kapitola 13.',
              en: 'A side panel opened from the action menu. It is used to search and sort accounts - see chapter 13.'
            } },
            { title: { cz: 'Stránkování', en: 'Pagination' }, text: {
              cz: 'Pod tabulkou přepínáte stránky a volíte počet záznamů na stránku. Koš má vlastní, nezávislé stránkování.',
              en: 'Below the table you switch pages and choose the number of records per page. The trash has its own independent pagination.'
            } },
            { title: { cz: 'Aktualizace dat', en: 'Refreshing data' }, text: {
              cz: 'U tabulky vidíte čas poslední aktualizace a tlačítko pro okamžité obnovení. Data se navíc sama obnovují přibližně každých 15 minut, pokud máte kartu prohlížeče otevřenou a aktivní. Tlačítko pro aktualizaci všeho v hlavičce administrace obnoví všechny tabulky najednou.',
              en: 'Next to the table you see the time of the last update and a button for an immediate refresh. The data also refreshes automatically roughly every 15 minutes while the browser tab is open and active. The refresh-all button in the administration header refreshes all tables at once.'
            } }
          ] },
          { type: 'text', content: {
            cz: 'Nadpis nad tabulkou vždy ukazuje, zda se díváte na aktivní účty, nebo na koš. Hromadné mazání více účtů najednou je na této stránce záměrně vypnuté - účty se mažou vždy po jednom.',
            en: 'The heading above the table always shows whether you are looking at active accounts or at the trash. Bulk deletion of several accounts at once is intentionally disabled on this page - accounts are always deleted one at a time.'
          } }
        ]
      },

      // ── 03 ──────────────────────────────────────────────────────────────
      {
        heading: { cz: '03. Životní cyklus účtu', en: '03. Account Lifecycle' },
        blocks: [
          { type: 'text', content: {
            cz: 'Každý účet prochází několika stavy. Když víte, ve kterém stavu účet je, víte i to, kterou akci použít.',
            en: 'Every account goes through several states. Once you know which state an account is in, you also know which action to use.'
          } },
          { type: 'flow', steps: [
            { label: { cz: 'Založený, čeká na aktivaci', en: 'Created, pending activation' }, text: {
              cz: 'Účet existuje, ale nemá heslo. Uživatel se nemůže přihlásit, dokud přes odkaz v aktivačním e-mailu nenastaví heslo. V řádku účtu je dostupná akce pro opětovné odeslání aktivace.',
              en: 'The account exists but has no password. The user cannot sign in until a password is set through the link in the activation e-mail. The row offers the action for resending the activation.'
            }, active: true },
            { label: { cz: 'Aktivní', en: 'Active' }, text: {
              cz: 'Uživatel si nastavil heslo a může se přihlašovat. Akce pro odeslání aktivace z řádku zmizí.',
              en: 'The user has set a password and can sign in. The resend-activation action disappears from the row.'
            } },
            { label: { cz: 'Blokovaný', en: 'Blocked' }, text: {
              cz: 'Volitelný a vratný stav. Uživatel je okamžitě odhlášen a nemůže se přihlásit, dokud blokaci nezrušíte. Účet zůstává v tabulce.',
              en: 'An optional and reversible state. The user is signed out immediately and cannot sign in until you remove the block. The account stays in the table.'
            } },
            { label: { cz: 'V koši', en: 'In the trash' }, text: {
              cz: 'Smazaný účet se přesune do koše. Uživatel se nepřihlásí, ale účet lze obnovit se vším nastavením.',
              en: 'A deleted account moves to the trash. The user cannot sign in, but the account can be restored with all its settings.'
            } },
            { label: { cz: 'Trvale smazaný', en: 'Permanently deleted' }, text: {
              cz: 'Účet je odstraněn z koše natrvalo. Tento krok nelze vrátit.',
              en: 'The account is removed from the trash for good. This step cannot be undone.'
            } }
          ] }
        ]
      },

      // ── 04 ──────────────────────────────────────────────────────────────
      {
        heading: { cz: '04. Založení nového účtu krok za krokem', en: '04. Creating a New Account Step by Step' },
        blocks: [
          { type: 'flow', steps: [
            { label: { cz: '1. Připravte si údaje', en: '1. Prepare the details' }, text: {
              cz: 'Ověřte si přesnou e-mailovou adresu nového uživatele - přijde na ni aktivační odkaz a zároveň slouží jako přihlašovací jméno. Rozmyslete si, jakou roli má uživatel dostat. Pokud systém omezuje e-mailové domény (kapitola 16), musí adresa patřit pod povolenou doménu, jinak účet nepůjde založit.',
              en: 'Verify the exact e-mail address of the new user - the activation link is sent to it and it also serves as the sign-in name. Decide which role the user should get. If the system restricts e-mail domains (chapter 16), the address must belong to an allowed domain, otherwise the account cannot be created.'
            } },
            { label: { cz: '2. Otevřete formulář', en: '2. Open the form' }, text: {
              cz: 'V nabídce akcí nad tabulkou zvolte položku pro vytvoření záznamu. Položka je vidět jen v zobrazení aktivních účtů (ne v koši) a jen pokud máte oprávnění zakládat účty.',
              en: 'In the action menu above the table, choose the item for creating a record. The item is visible only in the active accounts view (not in the trash) and only if you have the permission to create accounts.'
            } },
            { label: { cz: '3. Přečtěte si upozornění', en: '3. Read the notice' }, text: {
              cz: 'Nad formulářem se zobrazí informační pruh, který připomíná, že účet vzniká bez hesla. Heslo do formuláře nezadáváte - žádné pole pro něj ve formuláři není.',
              en: 'An information banner appears above the form, reminding you that the account is created without a password. You do not enter a password - the form has no field for it.'
            } },
            { label: { cz: '4. Přihlašovací e-mail (povinné)', en: '4. Sign-in e-mail (required)' }, text: {
              cz: 'Zadejte e-mail ve správném tvaru. Každý e-mail může mít jen jeden účet - pokud už účet s touto adresou existuje (i kdyby ležel v koši), systém uložení odmítne.',
              en: 'Enter the e-mail in a valid format. Each e-mail can have only one account - if an account with this address already exists (even one lying in the trash), the system refuses to save.'
            } },
            { label: { cz: '5. Celé jméno (povinné)', en: '5. Full name (required)' }, text: {
              cz: 'Jméno a příjmení uživatele. Zobrazuje se v tabulce, v detailu účtu a v oslovení v e-mailech.',
              en: 'The first and last name of the user. It is shown in the table, in the account details, and in the greeting of e-mails.'
            } },
            { label: { cz: '6. Role (povinné)', en: '6. Role (required)' }, text: {
              cz: 'Vyberte roli ze seznamu. Role určuje základní sadu oprávnění. V seznamu vidíte jen role, které smíte přidělit - tedy ty, jejichž všechna oprávnění sami máte. Roli sysadmin může přidělit pouze sysadmin.',
              en: 'Choose a role from the list. The role defines the basic set of permissions. The list shows only roles you are allowed to assign - those whose permissions you all hold yourself. The sysadmin role can be assigned only by a sysadmin.'
            } },
            { label: { cz: '7. Oprávnění navíc (nepovinné)', en: '7. Extra permissions (optional)' }, text: {
              cz: 'Po výběru role se v seznamu oprávnění automaticky zaškrtnou a uzamknou ta, která role už obsahuje. Zaškrtnutím dalších dáte uživateli něco navíc nad rámec role. Roli vybírejte vždy jako první - při každé změně role se výběr oprávnění vrátí do výchozího stavu nové role.',
              en: 'After you choose a role, the permissions the role already contains are ticked and locked automatically in the permission list. By ticking others you give the user something beyond the role. Always choose the role first - every role change returns the permission selection to the default state of the new role.'
            } },
            { label: { cz: '8. Dvoufázové ověření (nepovinné)', en: '8. Two-factor authentication (optional)' }, text: {
              cz: 'Zaškrtnutím zapnete uživateli ověřování kódem z e-mailu při každém přihlášení. U rolí, které dvoufázové ověření vyžadují (vždy sysadmin, případně další role podle jejich nastavení), je pole uzamčené a ověření bude u účtu zapnuté vždy - vypnout ho nejde.',
              en: 'Ticking it turns on verification by an e-mailed code at every sign-in. For roles that require two-factor authentication (always sysadmin, possibly other roles depending on their settings) the field is locked and the verification is always on for the account - it cannot be turned off.'
            } },
            { label: { cz: '9. Interní poznámka (nepovinné)', en: '9. Internal note (optional)' }, text: {
              cz: 'Volný text pro potřeby správců, například pracovní pozice nebo důvod založení účtu. Je vidět v detailu účtu. Nezapisujte do ní citlivé osobní údaje.',
              en: 'Free text for administrators, for example the job position or the reason the account was created. It is visible in the account details. Do not write sensitive personal data into it.'
            } },
            { label: { cz: '10. Uložte', en: '10. Save' }, text: {
              cz: 'Potvrďte formulář. Zobrazí se potvrzení o vytvoření účtu, formulář se zavře a nový účet se objeví v tabulce.',
              en: 'Confirm the form. A confirmation that the account was created appears, the form closes, and the new account shows up in the table.'
            } },
            { label: { cz: '11. Co se stane potom', en: '11. What happens next' }, text: {
              cz: 'Systém ihned odešle uživateli aktivační e-mail. Účet je založený, ale zatím neaktivní: není blokovaný, jen nemá heslo. Dejte uživateli vědět, ať zkontroluje poštu včetně složky s nevyžádanou poštou.',
              en: 'The system immediately sends the activation e-mail to the user. The account is created but not yet active: it is not blocked, it just has no password. Tell the user to check the inbox, including the spam folder.'
            } }
          ] },
          { type: 'alert', variant: 'info', content: {
            cz: 'Blokaci účtu a vynucení dvoufázového ověření pro konkrétní účet při zakládání nenastavíte - tato pole jsou dostupná až při úpravě existujícího účtu (kapitola 09).',
            en: 'You cannot set account blocking or forced two-factor authentication for a specific account during creation - these fields are available only when editing an existing account (chapter 09).'
          } },
          { type: 'alert', variant: 'info', content: {
            cz: 'Pokud uložení skončí hláškou o nepovolené e-mailové doméně, adresa nespadá pod povolené domény. Požádejte sysadmina o přidání výjimky a účet poté založte znovu.',
            en: 'If saving ends with a message about a disallowed e-mail domain, the address does not belong to the allowed domains. Ask a sysadmin to add an exception and then create the account again.'
          } },
          { type: 'alert', variant: 'info', content: {
            cz: 'Pokud uložení skončí hláškou, že nemůžete přidělit roli s oprávněními, která sami nemáte, vyberte jinou roli nebo požádejte o založení účtu sysadmina.',
            en: 'If saving ends with a message that you cannot assign a role granting permissions you do not have yourself, choose a different role or ask a sysadmin to create the account.'
          } }
        ]
      },

      // ── 05 ──────────────────────────────────────────────────────────────
      {
        heading: { cz: '05. Aktivace účtu - co udělá nový uživatel', en: '05. Account Activation - What the New User Does' },
        blocks: [
          { type: 'text', content: {
            cz: 'Tuto kapitolu můžete novému uživateli přeposlat nebo ho podle ní provést. Aktivační e-mail i aktivační stránka jsou v angličtině, proto jsou názvy tlačítek uvedeny anglicky.',
            en: 'You can forward this chapter to the new user or guide them through it. Both the activation e-mail and the activation page are in English.'
          } },
          { type: 'flow', steps: [
            { label: { cz: '1. Otevření e-mailu', en: '1. Opening the e-mail' }, text: {
              cz: 'E-mail uživatele osloví jménem, oznámí, že mu byl vytvořen účet, a obsahuje tlačítko „Set password and activate“. Pokud tlačítko nefunguje, je pod ním stejný odkaz k ručnímu zkopírování do prohlížeče.',
              en: 'The e-mail greets the user by name, announces that an account has been created, and contains the button "Set password and activate". If the button does not work, the same link is below it, ready to be copied into the browser.'
            } },
            { label: { cz: '2. Platnost odkazu', en: '2. Link validity' }, text: {
              cz: 'Odkaz platí omezenou dobu (počet hodin je uveden přímo v e-mailu) a lze ho použít jen jednou.',
              en: 'The link is valid for a limited time (the number of hours is stated in the e-mail) and can be used only once.'
            } },
            { label: { cz: '3. Ověření odkazu', en: '3. Link verification' }, text: {
              cz: 'Po kliknutí stránka krátce ověřuje odkaz. Je-li v pořádku, objeví se formulář „Set your password“ a pod nadpisem e-mail účtu, pro který se heslo nastavuje.',
              en: 'After the click the page briefly verifies the link. If it is fine, the form "Set your password" appears, with the e-mail of the account shown below the title.'
            } },
            { label: { cz: '4. Nastavení hesla', en: '4. Setting the password' }, text: {
              cz: 'Uživatel zadá nové heslo a pro kontrolu ho zopakuje. Pod prvním polem se průběžně odškrtávají splněné požadavky na heslo. Ikonou oka si může heslo zobrazit nebo skrýt. Pokud se obě hesla neshodují, stránka na to upozorní a formulář nejde odeslat.',
              en: 'The user enters a new password and repeats it for confirmation. Below the first field the fulfilled password requirements are ticked off live. The eye icon shows or hides the password. If the two passwords do not match, the page says so and the form cannot be submitted.'
            } },
            { label: { cz: '5. Odeslání', en: '5. Submitting' }, text: {
              cz: 'Tlačítkem „Set password and activate account“ uživatel aktivaci dokončí. Pokud heslo nesplňuje požadavky, stránka zobrazí důvod a heslo je potřeba upravit.',
              en: 'The button "Set password and activate account" completes the activation. If the password does not meet the requirements, the page shows the reason and the password must be adjusted.'
            } },
            { label: { cz: '6. Hotovo', en: '6. Done' }, text: {
              cz: 'Zobrazí se „Account activated“ a stránka uživatele po několika sekundách sama přesměruje na přihlášení (nebo lze kliknout na „Go to sign in now“). Uživatel není přihlášen automaticky - přihlásí se svým e-mailem a právě nastaveným heslem.',
              en: 'The page shows "Account activated" and redirects the user to the sign-in page after a few seconds (or the user can click "Go to sign in now"). The user is not signed in automatically - they sign in with their e-mail and the password they have just set.'
            } }
          ] },
          { type: 'grid', cards: [
            { title: { cz: 'Délka hesla', en: 'Password length' }, text: {
              cz: '8 až 16 znaků.',
              en: '8 to 16 characters.'
            } },
            { title: { cz: 'Písmeno', en: 'Letter' }, text: {
              cz: 'Heslo musí obsahovat alespoň jedno písmeno.',
              en: 'The password must contain at least one letter.'
            } },
            { title: { cz: 'Číslice', en: 'Digit' }, text: {
              cz: 'Heslo musí obsahovat alespoň jednu číslici.',
              en: 'The password must contain at least one digit.'
            } },
            { title: { cz: 'Speciální znak', en: 'Special character' }, text: {
              cz: 'Heslo musí obsahovat alespoň jeden speciální znak (například vykřičník nebo pomlčku).',
              en: 'The password must contain at least one special character (for example an exclamation mark or a hyphen).'
            } }
          ] },
          { type: 'alert', variant: 'info', content: {
            cz: 'Když odkaz vypršel, už byl použit nebo je poškozený, stránka oznámí, že odkaz nelze použít. Uživatel si nový odkaz sám vyžádat nemůže - musí požádat administrátora, který mu aktivaci pošle znovu (kapitola 06).',
            en: 'When the link has expired, has already been used, or is damaged, the page says the link cannot be used. The user cannot request a new link personally - they must ask an administrator, who resends the activation (chapter 06).'
          } },
          { type: 'note', content: {
            cz: 'Pokud někdo aktivační e-mail dostal a žádný účet nečekal, může zprávu bez obav ignorovat - bez kliknutí na odkaz a nastavení hesla se k účtu nikdo nepřihlásí.',
            en: 'If someone received the activation e-mail and was not expecting an account, they can safely ignore the message - without clicking the link and setting a password nobody can sign in to the account.'
          } }
        ]
      },

      // ── 06 ──────────────────────────────────────────────────────────────
      {
        heading: { cz: '06. Opětovné odeslání aktivačního e-mailu', en: '06. Resending the Activation E-mail' },
        blocks: [
          { type: 'text', content: {
            cz: 'Akce s ikonou obálky v řádku účtu. Je vidět jen u účtů, které ještě nebyly aktivovány, a jen pokud máte oprávnění upravovat účty.',
            en: 'The action with the envelope icon in the account row. It is visible only for accounts that have not been activated yet, and only if you have the permission to edit accounts.'
          } },
          { type: 'grid', cards: [
            { title: { cz: 'E-mail nedorazil', en: 'The e-mail did not arrive' }, text: {
              cz: 'Nejprve nechte uživatele zkontrolovat nevyžádanou poštu. Pak ověřte, že je e-mail v účtu napsaný správně, a aktivaci odešlete znovu.',
              en: 'First have the user check the spam folder. Then verify the e-mail in the account is spelled correctly and resend the activation.'
            } },
            { title: { cz: 'Odkaz vypršel', en: 'The link expired' }, text: {
              cz: 'Uživatel nestihl heslo nastavit v době platnosti odkazu. Odešlete aktivaci znovu.',
              en: 'The user did not manage to set the password while the link was valid. Resend the activation.'
            } },
            { title: { cz: 'Odkaz nejde použít', en: 'The link cannot be used' }, text: {
              cz: 'Odkaz byl už jednou otevřen a použit, nebo se při kopírování poškodil. Odešlete aktivaci znovu.',
              en: 'The link has already been opened and used once, or was damaged when copied. Resend the activation.'
            } },
            { title: { cz: 'Opravili jste e-mail', en: 'You corrected the e-mail' }, text: {
              cz: 'Pokud byl účet založen s překlepem v adrese, nejprve e-mail opravte v úpravě účtu a potom odešlete aktivaci znovu - přijde už na správnou adresu.',
              en: 'If the account was created with a typo in the address, first correct the e-mail by editing the account and then resend the activation - it will go to the correct address.'
            } }
          ] },
          { type: 'flow', steps: [
            { label: { cz: '1. Najděte účet', en: '1. Find the account' }, text: {
              cz: 'Vyhledejte účet v tabulce, případně pomocí filtru podle jména nebo e-mailu.',
              en: 'Find the account in the table, using the filter by name or e-mail if needed.'
            } },
            { label: { cz: '2. Klikněte na obálku', en: '2. Click the envelope' }, text: {
              cz: 'V řádku účtu klikněte na akci pro odeslání aktivace.',
              en: 'In the account row, click the resend-activation action.'
            } },
            { label: { cz: '3. Potvrzení', en: '3. Confirmation' }, text: {
              cz: 'Systém potvrdí, že byl aktivační e-mail odeslán znovu.',
              en: 'The system confirms that the activation e-mail has been resent.'
            } },
            { label: { cz: '4. Starý odkaz přestává platit', en: '4. The old link stops working' }, text: {
              cz: 'Uživatel musí použít odkaz z nejnovějšího e-mailu. Všechny dříve zaslané aktivační odkazy jsou od této chvíle neplatné.',
              en: 'The user must use the link from the newest e-mail. All activation links sent earlier are invalid from this moment.'
            } }
          ] },
          { type: 'alert', variant: 'info', content: {
            cz: 'U účtu, který už aktivovaný je, systém pouze oznámí, že účet je aktivní, a nic neodešle. Zapomenuté heslo aktivovaného účtu řeší kapitola 11. Pokud se e-mail nepodaří odeslat, zobrazí se chyba - zkuste to později, a pokud potíž trvá, kontaktujte sysadmina.',
            en: 'For an account that is already activated, the system only states that the account is active and sends nothing. A forgotten password of an activated account is covered in chapter 11. If the e-mail fails to send, an error is shown - try again later and contact a sysadmin if the problem persists.'
          } }
        ]
      },

      // ── 07 ──────────────────────────────────────────────────────────────
      {
        heading: { cz: '07. Role a oprávnění navíc', en: '07. Roles and Extra Permissions' },
        blocks: [
          { type: 'text', content: {
            cz: 'Každý účet má právě jednu roli. Role je pojmenovaná sada oprávnění a určuje, co uživatel v administraci vidí a smí dělat. K roli lze jednotlivému účtu přidat oprávnění navíc - hodí se, když jeden člověk potřebuje výjimečně něco, co jeho role neobsahuje. Role samotné se na této stránce nevytvářejí ani neupravují, zde je pouze přidělujete.',
            en: 'Every account has exactly one role. A role is a named set of permissions and determines what the user sees and may do in the administration. On top of the role, extra permissions can be added to an individual account - useful when one person exceptionally needs something the role does not contain. Roles themselves are not created or edited on this page; here you only assign them.'
          } },
          { type: 'grid', cards: [
            { title: { cz: 'Které role mohu přidělit', en: 'Which roles I can assign' }, text: {
              cz: 'Jen role, jejichž všechna oprávnění sami máte. Roli, která by někomu dala víc, než máte vy, v seznamu neuvidíte (při úpravě účtu se navíc zobrazí jeho současná role). Sysadmin může přidělit jakoukoli roli.',
              en: 'Only roles whose permissions you all hold yourself. A role that would give someone more than you have is not shown in the list (when editing an account, its current role is shown as well). A sysadmin can assign any role.'
            } },
            { title: { cz: 'Role sysadmin', en: 'The sysadmin role' }, text: {
              cz: 'Přidělit ji novému účtu, povýšit na ni existující účet nebo upravit účet, který ji má, smí pouze sysadmin.',
              en: 'Only a sysadmin may assign it to a new account, promote an existing account to it, or edit an account that has it.'
            } },
            { title: { cz: 'Která oprávnění navíc mohu dát', en: 'Which extra permissions I can give' }, text: {
              cz: 'Přidat nebo odebrat smíte jen oprávnění, která sami máte. Pokud zaškrtnete oprávnění mimo svůj dosah, neuloží se. Oprávnění, která účtu dříve přidělil někdo s širšími právy a vy je nemáte, zůstanou beze změny.',
              en: 'You may add or remove only permissions you hold yourself. If you tick a permission outside your reach, it is not saved. Permissions that someone with wider rights granted earlier and that you do not hold stay unchanged.'
            } },
            { title: { cz: 'Zaškrtnutá a uzamčená oprávnění', en: 'Ticked and locked permissions' }, text: {
              cz: 'Jsou to oprávnění, která obsahuje role. Jednotlivě je odebrat nelze - změní se jen změnou role.',
              en: 'These are the permissions contained in the role. They cannot be removed individually - they change only when the role changes.'
            } },
            { title: { cz: 'Vlastní účet', en: 'Your own account' }, text: {
              cz: 'Vlastní roli si změnit nemůžete. Potřebujete-li jinou roli, požádejte jiného oprávněného administrátora.',
              en: 'You cannot change your own role. If you need a different role, ask another authorised administrator.'
            } }
          ] },
          { type: 'flow', steps: [
            { label: { cz: '1. Otevřete úpravu účtu', en: '1. Open the account for editing' }, text: {
              cz: 'V řádku účtu klikněte na akci úpravy.',
              en: 'In the account row, click the edit action.'
            } },
            { label: { cz: '2. Vyberte novou roli', en: '2. Choose the new role' }, text: {
              cz: 'Seznam oprávnění se okamžitě přepočítá: dříve vybraná oprávnění navíc se zruší a zaškrtnutá zůstanou jen oprávnění nové role.',
              en: 'The permission list is recalculated immediately: previously selected extra permissions are cleared and only the permissions of the new role stay ticked.'
            } },
            { label: { cz: '3. Uložte', en: '3. Save' }, text: {
              cz: 'Systém zobrazí oznámení, že se změnou role byla všechna oprávnění navíc vynulována, a potvrdí aktualizaci účtu.',
              en: 'The system shows a notice that all extra permissions were reset with the role change, and confirms the account update.'
            } },
            { label: { cz: '4. Případně přidejte oprávnění navíc', en: '4. Add extra permissions if needed' }, text: {
              cz: 'Potřebuje-li uživatel i v nové roli něco navíc, otevřete úpravu účtu znovu, oprávnění zaškrtněte a uložte. V jednom kroku se změnou role to nejde.',
              en: 'If the user needs something extra in the new role as well, open the account for editing again, tick the permissions, and save. This cannot be done in the same step as the role change.'
            } }
          ] },
          { type: 'alert', variant: 'info', content: {
            cz: 'Změna role vždy smaže všechna oprávnění navíc. Je to záměr - uživatel si do nové role nepřenáší výjimky z té staré.',
            en: 'A role change always removes all extra permissions. This is intentional - the user does not carry exceptions from the old role into the new one.'
          } }
        ]
      },

      // ── 08 ──────────────────────────────────────────────────────────────
      {
        heading: { cz: '08. Dvoufázové ověření (2FA)', en: '08. Two-Factor Authentication (2FA)' },
        blocks: [
          { type: 'text', content: {
            cz: 'Dvoufázové ověření přidává k heslu druhý krok: po zadání e-mailu a hesla přijde uživateli na e-mail jednorázový kód, bez kterého se nepřihlásí. I kdyby někdo heslo uhodl nebo ukradl, bez přístupu k e-mailové schránce se do účtu nedostane.',
            en: 'Two-factor authentication adds a second step to the password: after entering the e-mail and password, the user receives a one-time code by e-mail, without which the sign-in cannot be completed. Even if someone guesses or steals the password, they cannot get into the account without access to the mailbox.'
          } },
          { type: 'grid', cards: [
            { title: { cz: 'Dobrovolné', en: 'Optional' }, text: {
              cz: 'Zaškrtávací pole pro dvoufázové ověření ve formuláři účtu lze zapnout i vypnout. Platí pro účty, u kterých ověření není vynucené.',
              en: 'The two-factor authentication checkbox in the account form can be turned on and off. This applies to accounts where the verification is not forced.'
            } },
            { title: { cz: 'Vynucené rolí', en: 'Forced by the role' }, text: {
              cz: 'Role sysadmin ho má zapnuté vždy. Vyžadovat ho mohou i další role, pokud je tak nastavil sysadmin. Pole je pak uzamčené, ověření je u účtu vždy zapnuté a vypnout ho nelze.',
              en: 'The sysadmin role always has it on. Other roles may require it as well if a sysadmin configured them so. The field is then locked, the verification is always on for the account, and it cannot be turned off.'
            } },
            { title: { cz: 'Vynucené pro konkrétní účet', en: 'Forced for a specific account' }, text: {
              cz: 'Sysadmin může při úpravě účtu, jehož role ověření nevyžaduje, zaškrtnout pole pro vynucení. Účet má pak ověření trvale zapnuté a vypnout ho smí zase jen sysadmin. Toto pole vidí pouze sysadmin, jen při úpravě (ne při zakládání) a jen u rolí, které ověření samy nevynucují.',
              en: 'When editing an account whose role does not require the verification, a sysadmin can tick the force field. The account then has the verification permanently on and only a sysadmin may turn it off again. Only a sysadmin sees this field, only when editing (not when creating), and only for roles that do not force the verification themselves.'
            } }
          ] },
          { type: 'flow', steps: [
            { label: { cz: '1. E-mail a heslo', en: '1. E-mail and password' }, text: {
              cz: 'Uživatel se na přihlašovací stránce přihlásí e-mailem a heslem jako obvykle.',
              en: 'The user signs in on the sign-in page with e-mail and password as usual.'
            } },
            { label: { cz: '2. Kód přijde e-mailem', en: '2. The code arrives by e-mail' }, text: {
              cz: 'Na e-mail účtu dorazí zpráva se šestimístným ověřovacím kódem.',
              en: 'A message with a six-digit verification code arrives at the e-mail of the account.'
            } },
            { label: { cz: '3. Zadání kódu', en: '3. Entering the code' }, text: {
              cz: 'Přihlašovací stránka zobrazí pole pro kód a odpočet, jak dlouho kód ještě platí. Po zadání všech šesti číslic uživatel přihlášení potvrdí.',
              en: 'The sign-in page shows a field for the code and a countdown of how long the code remains valid. After entering all six digits the user confirms the sign-in.'
            } },
            { label: { cz: '4. Kód nepřišel nebo vypršel', en: '4. The code did not arrive or expired' }, text: {
              cz: 'Tlačítkem pro opětovné odeslání si uživatel vyžádá nový kód. Tlačítko je aktivní až po 60 sekundách od posledního odeslání - do té doby u něj běží odpočet.',
              en: 'With the resend button the user requests a new code. The button becomes active 60 seconds after the last sending - until then a countdown runs next to it.'
            } },
            { label: { cz: '5. Návrat zpět', en: '5. Going back' }, text: {
              cz: 'Tlačítkem zpět se uživatel vrátí k zadání e-mailu a hesla, například když se přihlašoval k nesprávnému účtu.',
              en: 'With the back button the user returns to entering the e-mail and password, for example after signing in to the wrong account.'
            } }
          ] },
          { type: 'alert', variant: 'info', content: {
            cz: 'Ověřovací kód nikdy nikomu nesdělujte. Pokud uživateli přijde kód, aniž by se sám přihlašoval, někdo zná jeho heslo - má si ho ihned změnit.',
            en: 'Never share the verification code with anyone. If a user receives a code without trying to sign in, someone knows their password - they should change it immediately.'
          } },
          { type: 'note', content: {
            cz: 'Po několika neúspěšných pokusech o přihlášení může přihlašovací stránka navíc vyžadovat ověření, že se nepřihlašuje robot. Jde o běžnou ochranu, po úspěšném ověření se přihlášení dokončí normálně.',
            en: 'After several failed sign-in attempts the sign-in page may additionally require a check that the visitor is not a robot. This is a standard protection; once the check passes, the sign-in completes normally.'
          } }
        ]
      },

      // ── 09 ──────────────────────────────────────────────────────────────
      {
        heading: { cz: '09. Úprava existujícího účtu', en: '09. Editing an Existing Account' },
        blocks: [
          { type: 'flow', steps: [
            { label: { cz: '1. Otevřete úpravu', en: '1. Open the edit form' }, text: {
              cz: 'V řádku účtu klikněte na akci úpravy. Akce je vidět jen s oprávněním upravovat účty.',
              en: 'In the account row, click the edit action. The action is visible only with the permission to edit accounts.'
            } },
            { label: { cz: '2. Zkontrolujte předvyplněné údaje', en: '2. Check the pre-filled data' }, text: {
              cz: 'Formulář se otevře s aktuálními údaji účtu. V seznamu oprávnění jsou zaškrtnutá oprávnění z role (uzamčená) i oprávnění navíc (lze je měnit).',
              en: 'The form opens with the current data of the account. The permission list shows the role permissions ticked (locked) as well as the extra permissions (changeable).'
            } },
            { label: { cz: '3. Upravte, co potřebujete', en: '3. Change what you need' }, text: {
              cz: 'Měnit lze jen pole, která nejsou uzamčená. Význam jednotlivých polí je popsán níže.',
              en: 'Only fields that are not locked can be changed. The meaning of each field is described below.'
            } },
            { label: { cz: '4. Uložte', en: '4. Save' }, text: {
              cz: 'Po uložení se zobrazí potvrzení o aktualizaci účtu, formulář se zavře a tabulka se obnoví. Tlačítkem pro zrušení formulář zavřete beze změn.',
              en: 'After saving, a confirmation of the account update appears, the form closes, and the table refreshes. The cancel button closes the form without changes.'
            } }
          ] },
          { type: 'grid', cards: [
            { title: { cz: 'E-mail', en: 'E-mail' }, text: {
              cz: 'Změna přihlašovacího e-mailu. Adresa musí být jedinečná. Omezení povolených domén se při úpravě nekontroluje, platí jen pro zakládání účtů.',
              en: 'Change of the sign-in e-mail. The address must be unique. The allowed-domain restriction is not checked when editing; it applies only to creating accounts.'
            } },
            { title: { cz: 'Celé jméno', en: 'Full name' }, text: {
              cz: 'Oprava nebo změna jména uživatele.',
              en: 'Correction or change of the user name.'
            } },
            { title: { cz: 'Role a oprávnění navíc', en: 'Role and extra permissions' }, text: {
              cz: 'Viz kapitola 07. Pamatujte, že změna role smaže oprávnění navíc.',
              en: 'See chapter 07. Remember that a role change removes the extra permissions.'
            } },
            { title: { cz: 'Dvoufázové ověření', en: 'Two-factor authentication' }, text: {
              cz: 'Viz kapitola 08. U účtů s vynuceným ověřením je pole uzamčené.',
              en: 'See chapter 08. For accounts with forced verification the field is locked.'
            } },
            { title: { cz: 'Vynucení dvoufázového ověření', en: 'Forcing two-factor authentication' }, text: {
              cz: 'Pole vidí jen sysadmin a jen u účtů, jejichž role ověření sama nevynucuje.',
              en: 'Only a sysadmin sees the field, and only for accounts whose role does not force the verification itself.'
            } },
            { title: { cz: 'Blokace', en: 'Blocking' }, text: {
              cz: 'Viz kapitola 10. U účtů s rolí sysadmin je pole uzamčené.',
              en: 'See chapter 10. For accounts with the sysadmin role the field is locked.'
            } },
            { title: { cz: 'Interní poznámka', en: 'Internal note' }, text: {
              cz: 'Volný text pro správce, viditelný v detailu účtu.',
              en: 'Free text for administrators, visible in the account details.'
            } }
          ] },
          { type: 'alert', variant: 'info', content: {
            cz: 'Účet s rolí sysadmin smí upravovat pouze sysadmin. Ostatním systém úpravu odmítne a pokus zaznamená.',
            en: 'An account with the sysadmin role may be edited only by a sysadmin. For everyone else the system refuses the edit and records the attempt.'
          } }
        ]
      },

      // ── 10 ──────────────────────────────────────────────────────────────
      {
        heading: { cz: '10. Blokace a odblokování účtu', en: '10. Blocking and Unblocking an Account' },
        blocks: [
          { type: 'text', content: {
            cz: 'Blokace je rychlý a vratný způsob, jak někomu okamžitě zabránit v přístupu, aniž byste účet mazali. Účet zůstává v tabulce se vším nastavením.',
            en: 'Blocking is a fast and reversible way to cut off access immediately without deleting the account. The account stays in the table with all its settings.'
          } },
          { type: 'grid', cards: [
            { title: { cz: 'Kdy blokovat', en: 'When to block' }, text: {
              cz: 'Při podezření na zneužití účtu nebo únik hesla, při dočasné nepřítomnosti uživatele, nebo jako první krok při ukončení spolupráce, než se rozhodne o smazání.',
              en: 'When misuse of the account or a password leak is suspected, during a temporary absence of the user, or as the first step when a cooperation ends, before deletion is decided.'
            } },
            { title: { cz: 'Co se stane', en: 'What happens' }, text: {
              cz: 'Uživatel je okamžitě odhlášen na všech zařízeních a nemůže se znovu přihlásit, dokud blokace trvá.',
              en: 'The user is signed out immediately on all devices and cannot sign in again while the block lasts.'
            } },
            { title: { cz: 'Co zablokovat nejde', en: 'What cannot be blocked' }, text: {
              cz: 'Vlastní účet zablokovat nemůžete. Účty s rolí sysadmin nelze zablokovat nikdy - pole je u nich uzamčené.',
              en: 'You cannot block your own account. Accounts with the sysadmin role can never be blocked - the field is locked for them.'
            } },
            { title: { cz: 'Odblokování', en: 'Unblocking' }, text: {
              cz: 'V úpravě účtu zrušte zaškrtnutí blokace a uložte. Uživatel se pak přihlásí svým původním heslem.',
              en: 'Edit the account, untick the block, and save. The user then signs in with the original password.'
            } }
          ] },
          { type: 'flow', steps: [
            { label: { cz: '1. Otevřete úpravu účtu', en: '1. Open the account for editing' }, text: {
              cz: 'Blokace se nastavuje pouze v úpravě existujícího účtu, při zakládání ji nenajdete.',
              en: 'Blocking is set only when editing an existing account; it is not available during creation.'
            } },
            { label: { cz: '2. Zaškrtněte blokaci', en: '2. Tick the block' }, text: {
              cz: 'Zaškrtněte pole pro zablokování účtu.',
              en: 'Tick the field for blocking the account.'
            } },
            { label: { cz: '3. Uložte', en: '3. Save' }, text: {
              cz: 'Blokace platí okamžitě po uložení.',
              en: 'The block applies immediately after saving.'
            } },
            { label: { cz: '4. Ověřte výsledek', en: '4. Verify the result' }, text: {
              cz: 'Ve sloupci blokace v tabulce uvidíte, že je účet blokovaný. Všechny blokované účty zobrazíte filtrem podle blokace.',
              en: 'The blocked column in the table shows that the account is blocked. Use the blocked filter to list all blocked accounts.'
            } }
          ] }
        ]
      },

      // ── 11 ──────────────────────────────────────────────────────────────
      {
        heading: { cz: '11. Hesla - zapomenuté heslo a změna hesla', en: '11. Passwords - Forgotten Password and Password Change' },
        blocks: [
          { type: 'text', content: {
            cz: 'Heslo lze řešit třemi cestami. Vyberte podle situace:',
            en: 'A password can be handled in three ways. Choose according to the situation:'
          } },
          { type: 'grid', cards: [
            { title: { cz: 'Uživatel zapomněl heslo', en: 'The user forgot the password' }, text: {
              cz: 'Uživatel si heslo obnoví sám z přihlašovací stránky. Je to doporučená cesta - nové heslo nezná nikdo jiný a administrátor nemusí nic dělat.',
              en: 'The user resets the password personally from the sign-in page. This is the recommended way - nobody else knows the new password and the administrator does not need to do anything.'
            } },
            { title: { cz: 'Heslo musí změnit administrátor', en: 'An administrator must change the password' }, text: {
              cz: 'Použijte, když se uživatel nedostane ke své e-mailové schránce, nebo když je třeba heslo změnit okamžitě (například při podezření na únik). Heslo změníte akcí s ikonou klíče.',
              en: 'Use it when the user cannot reach their mailbox, or when the password must be changed immediately (for example when a leak is suspected). You change the password with the key icon action.'
            } },
            { title: { cz: 'Účet nebyl nikdy aktivován', en: 'The account was never activated' }, text: {
              cz: 'Takový účet ještě žádné heslo nemá. Neřešte ho změnou hesla - odešlete znovu aktivační e-mail (kapitola 06).',
              en: 'Such an account has no password yet. Do not handle it with a password change - resend the activation e-mail (chapter 06).'
            } }
          ] },
          { type: 'text', content: {
            cz: 'Zapomenuté heslo - postup uživatele:',
            en: 'Forgotten password - what the user does:'
          } },
          { type: 'flow', steps: [
            { label: { cz: '1. Odkaz na přihlašovací stránce', en: '1. The link on the sign-in page' }, text: {
              cz: 'U pole pro heslo uživatel klikne na odkaz pro zapomenuté heslo. Otevře se malé okno.',
              en: 'Next to the password field the user clicks the forgotten-password link. A small window opens.'
            } },
            { label: { cz: '2. Zadání e-mailu', en: '2. Entering the e-mail' }, text: {
              cz: 'Uživatel zadá e-mail svého účtu a žádost odešle. Okno potvrdí odeslání a po chvíli se samo zavře.',
              en: 'The user enters the e-mail of the account and submits the request. The window confirms the sending and closes itself after a moment.'
            } },
            { label: { cz: '3. E-mail s odkazem', en: '3. The e-mail with the link' }, text: {
              cz: 'Do schránky přijde zpráva s tlačítkem „Reset your password“. Odkaz platí omezenou dobu (počet minut je uveden v e-mailu) a lze ho použít jen jednou. Pokud uživatel o obnovu nežádal, zprávu ignoruje - heslo zůstane beze změny.',
              en: 'A message with the button "Reset your password" arrives in the mailbox. The link is valid for a limited time (the number of minutes is stated in the e-mail) and can be used only once. If the user did not request the reset, they ignore the message - the password stays unchanged.'
            } },
            { label: { cz: '4. Nové heslo', en: '4. The new password' }, text: {
              cz: 'Na stránce „Set a new password“ uživatel zadá nové heslo a zopakuje ho. Platí stejné požadavky jako při aktivaci: 8 až 16 znaků, písmeno, číslice a speciální znak. Tlačítko „Set new password“ je aktivní až ve chvíli, kdy heslo splňuje všechny požadavky a obě pole se shodují.',
              en: 'On the page "Set a new password" the user enters the new password and repeats it. The same requirements apply as during activation: 8 to 16 characters, a letter, a digit, and a special character. The button "Set new password" becomes active only when the password meets all requirements and both fields match.'
            } },
            { label: { cz: '5. Potvrzení', en: '5. Confirmation' }, text: {
              cz: 'Stránka zobrazí „Password changed“ a po chvíli uživatele přesměruje na přihlášení.',
              en: 'The page shows "Password changed" and redirects the user to the sign-in page after a moment.'
            } },
            { label: { cz: '6. Neplatný odkaz', en: '6. Invalid link' }, text: {
              cz: 'Pokud odkaz vypršel nebo už byl použit, stránka to oznámí po odeslání formuláře. Uživatel se vrátí na přihlašovací stránku a o obnovu požádá znovu.',
              en: 'If the link has expired or has already been used, the page says so after the form is submitted. The user returns to the sign-in page and requests the reset again.'
            } }
          ] },
          { type: 'text', content: {
            cz: 'Změna hesla administrátorem - postup:',
            en: 'Password change by an administrator - procedure:'
          } },
          { type: 'flow', steps: [
            { label: { cz: '1. Klikněte na klíč', en: '1. Click the key' }, text: {
              cz: 'V řádku účtu klikněte na akci s ikonou klíče. Akce je vidět jen s oprávněním upravovat účty.',
              en: 'In the account row, click the action with the key icon. The action is visible only with the permission to edit accounts.'
            } },
            { label: { cz: '2. Zkontrolujte účet', en: '2. Check the account' }, text: {
              cz: 'V nadpisu formuláře je e-mail účtu, kterému heslo měníte. Ujistěte se, že jde o správný účet.',
              en: 'The form title contains the e-mail of the account whose password you are changing. Make sure it is the right account.'
            } },
            { label: { cz: '3. Zadejte SVÉ aktuální heslo', en: '3. Enter YOUR current password' }, text: {
              cz: 'První pole slouží k potvrzení, že změnu provádíte opravdu vy. Zadejte do něj své vlastní přihlašovací heslo - ne heslo uživatele, kterému heslo měníte.',
              en: 'The first field confirms that it is really you making the change. Enter your own sign-in password - not the password of the user whose password you are changing.'
            } },
            { label: { cz: '4. Zadejte nové heslo', en: '4. Enter the new password' }, text: {
              cz: 'Nové heslo zadejte a pro kontrolu zopakujte. Musí mít 8 až 16 znaků a obsahovat písmeno, číslici a speciální znak.',
              en: 'Enter the new password and repeat it for confirmation. It must have 8 to 16 characters and contain a letter, a digit, and a special character.'
            } },
            { label: { cz: '5. Uložte', en: '5. Save' }, text: {
              cz: 'Systém potvrdí, že heslo bylo změněno. Pokud jste své heslo v prvním poli zadali špatně, změna se neprovede a zobrazí se chyba.',
              en: 'The system confirms that the password has been changed. If you entered your own password in the first field incorrectly, the change is not made and an error is shown.'
            } },
            { label: { cz: '6. Předejte heslo bezpečně', en: '6. Hand over the password safely' }, text: {
              cz: 'Nové heslo sdělte uživateli bezpečnou cestou (osobně nebo telefonicky, ne e-mailem) a požádejte ho, ať si ho co nejdříve změní na vlastní.',
              en: 'Tell the user the new password in a safe way (in person or by phone, not by e-mail) and ask them to change it to their own as soon as possible.'
            } }
          ] },
          { type: 'alert', variant: 'info', content: {
            cz: 'Po každé změně hesla dostane majitel účtu e-mailem oznámení s datem a časem změny. Pokud změnu neprovedl on ani administrátor na jeho žádost, má se ihned ozvat - účet v takovém případě zablokujte (kapitola 10) a heslo změňte. Při mnoha změnách hesla v krátké době může systém další oznámení dočasně neposílat.',
            en: 'After every password change the account owner receives an e-mail notification with the date and time of the change. If neither the owner nor an administrator acting on their request made the change, the owner should report it immediately - in that case block the account (chapter 10) and change the password. With many password changes in a short time the system may temporarily stop sending further notifications.'
          } },
          { type: 'alert', variant: 'info', content: {
            cz: 'Heslo účtu s rolí sysadmin smí změnit jen jeho majitel nebo jiný sysadmin.',
            en: 'The password of an account with the sysadmin role may be changed only by its owner or by another sysadmin.'
          } }
        ]
      },

      // ── 12 ──────────────────────────────────────────────────────────────
      {
        heading: { cz: '12. Detail účtu', en: '12. Account Details' },
        blocks: [
          { type: 'text', content: {
            cz: 'Akce s ikonou lupy v řádku otevře přehled všech údajů účtu. Detail je pouze ke čtení - nic v něm nelze změnit - a zavřete ho tlačítkem pro zavření.',
            en: 'The action with the magnifier icon in the row opens an overview of all data of the account. The details are read-only - nothing can be changed there - and you close them with the close button.'
          } },
          { type: 'grid', cards: [
            { title: { cz: 'Základní údaje', en: 'Basic data' }, text: {
              cz: 'ID účtu, celé jméno a přihlašovací e-mail.',
              en: 'Account ID, full name, and sign-in e-mail.'
            } },
            { title: { cz: 'Role a oprávnění navíc', en: 'Role and extra permissions' }, text: {
              cz: 'Přidělená role a seznam oprávnění, která účet dostal nad rámec role.',
              en: 'The assigned role and the list of permissions the account received beyond the role.'
            } },
            { title: { cz: 'Stav účtu', en: 'Account state' }, text: {
              cz: 'Zda je účet blokovaný a datum aktivace. Prázdné datum aktivace znamená, že si uživatel ještě nenastavil heslo.',
              en: 'Whether the account is blocked and the activation date. An empty activation date means the user has not set a password yet.'
            } },
            { title: { cz: 'Dvoufázové ověření', en: 'Two-factor authentication' }, text: {
              cz: 'Zda je ověření u účtu zapnuté a zda ho pro tento účet vynutil sysadmin.',
              en: 'Whether the verification is on for the account and whether a sysadmin forced it for this account.'
            } },
            { title: { cz: 'Interní poznámka', en: 'Internal note' }, text: {
              cz: 'Text, který k účtu zapsali správci.',
              en: 'The text administrators wrote for the account.'
            } },
            { title: { cz: 'Data vytvoření a změny', en: 'Created and updated dates' }, text: {
              cz: 'Kdy byl účet založen a kdy byl naposledy upraven.',
              en: 'When the account was created and when it was last modified.'
            } }
          ] }
        ]
      },

      // ── 13 ──────────────────────────────────────────────────────────────
      {
        heading: { cz: '13. Filtry, řazení a hledání', en: '13. Filters, Sorting, and Search' },
        blocks: [
          { type: 'flow', steps: [
            { label: { cz: '1. Otevřete filtry', en: '1. Open the filters' }, text: {
              cz: 'V nabídce akcí zvolte položku pro filtry. Vedle tabulky se otevře boční panel. Stejnou položkou (její název se změní na skrytí filtrů) panel zase zavřete.',
              en: 'In the action menu choose the filters item. A side panel opens next to the table. The same item (its label changes to hiding the filters) closes the panel again.'
            } },
            { label: { cz: '2. Zadejte podmínky', en: '2. Enter the conditions' }, text: {
              cz: 'Filtrovat lze podle jména a e-mailu (stačí část textu), podle role (výběr ze seznamu) a podle toho, zda je účet blokovaný (ano nebo ne). Podmínky lze kombinovat.',
              en: 'You can filter by name and e-mail (a part of the text is enough), by role (chosen from a list), and by whether the account is blocked (yes or no). Conditions can be combined.'
            } },
            { label: { cz: '3. Zvolte řazení', en: '3. Choose the sorting' }, text: {
              cz: 'V panelu vyberete sloupec, podle kterého se má tabulka seřadit, a směr řazení. Výchozí řazení je od nejnovějšího účtu.',
              en: 'In the panel you choose the column to sort the table by and the direction. The default order is from the newest account.'
            } },
            { label: { cz: '4. Použijte filtry', en: '4. Apply the filters' }, text: {
              cz: 'Po potvrzení se tabulka načte znovu jen s odpovídajícími účty. Filtry zůstávají platné i při přechodu na další stránku a při změně počtu záznamů na stránku.',
              en: 'After confirming, the table reloads with matching accounts only. The filters stay in effect when you move to another page and when you change the number of records per page.'
            } },
            { label: { cz: '5. Zrušte filtry', en: '5. Clear the filters' }, text: {
              cz: 'Tlačítkem pro vymazání filtrů se vrátíte k úplnému seznamu ve výchozím řazení.',
              en: 'The clear-filters button returns you to the complete list in the default order.'
            } }
          ] },
          { type: 'note', content: {
            cz: 'Tip: hledání nad tabulkou prohledává jméno a e-mail. Podle role nehledá - k tomu použijte filtr podle role.',
            en: 'Tip: the search above the table looks in the name and the e-mail. It does not search by role - use the role filter for that.'
          } }
        ]
      },

      // ── 14 ──────────────────────────────────────────────────────────────
      {
        heading: { cz: '14. Export dat a reporty', en: '14. Data Export and Reports' },
        blocks: [
          { type: 'grid', cards: [
            { title: { cz: 'Export dat', en: 'Data export' }, text: {
              cz: 'Položka pro export v nabídce akcí stáhne tabulku aktivních účtů jako soubor CSV, který otevřete v tabulkovém programu. Role a oprávnění součástí exportu nejsou. Export je dostupný jen v zobrazení aktivních účtů, ne v koši.',
              en: 'The export item in the action menu downloads the table of active accounts as a CSV file that you can open in a spreadsheet program. Roles and permissions are not part of the export. The export is available only in the active accounts view, not in the trash.'
            } },
            { title: { cz: 'Zacházení s exportem', en: 'Handling the export' }, text: {
              cz: 'Soubor obsahuje osobní údaje (jména a e-maily). Ukládejte ho jen na místa určená pro pracovní data, neposílejte ho mimo firmu a po použití ho smažte.',
              en: 'The file contains personal data (names and e-mails). Store it only in places intended for work data, do not send it outside the company, and delete it after use.'
            } },
            { title: { cz: 'Reporty', en: 'Reports' }, text: {
              cz: 'Položka pro reporty otevře nástroj pro tvorbu grafů nad účty. Lze sledovat, kolik účtů je blokovaných, kolik jich má zapnuté dvoufázové ověření a kolik ho má vynucené, a to podle data vytvoření účtu. Nástroj zavřete jeho tlačítkem pro zavření.',
              en: 'The reports item opens the chart builder for accounts. You can see how many accounts are blocked, how many have two-factor authentication turned on, and how many have it forced, by the date the account was created. Close the tool with its close button.'
            } }
          ] }
        ]
      },

      // ── 15 ──────────────────────────────────────────────────────────────
      {
        heading: { cz: '15. Smazání účtu, koš, obnova a trvalé smazání', en: '15. Deleting an Account, Trash, Restore, and Permanent Deletion' },
        blocks: [
          { type: 'text', content: {
            cz: 'Mazání má dva stupně. Běžné smazání účet jen přesune do koše, odkud ho lze vrátit. Teprve trvalé smazání z koše je konečné.',
            en: 'Deletion has two levels. A regular delete only moves the account to the trash, from which it can be brought back. Only permanent deletion from the trash is final.'
          } },
          { type: 'flow', steps: [
            { label: { cz: '1. Smazání do koše', en: '1. Deleting to the trash' }, text: {
              cz: 'V řádku účtu klikněte na akci smazání (vyžaduje oprávnění mazat účty). Účet zmizí z tabulky aktivních účtů a přesune se do koše. Smazaný uživatel se už nepřihlásí.',
              en: 'In the account row, click the delete action (requires the permission to delete accounts). The account disappears from the active accounts table and moves to the trash. The deleted user can no longer sign in.'
            } },
            { label: { cz: '2. Zobrazení koše', en: '2. Viewing the trash' }, text: {
              cz: 'V nabídce akcí přepněte na koš (vyžaduje oprávnění zobrazit smazané záznamy). Nadpis nad tabulkou se změní a tabulka ukáže ID, jméno, e-mail a datum smazání. V zobrazení koše v nabídce akcí nejsou položky pro vytvoření záznamu a export.',
              en: 'In the action menu switch to the trash (requires the permission to view deleted records). The heading above the table changes and the table shows the ID, name, e-mail, and deletion date. In the trash view the action menu does not offer creating a record or exporting.'
            } },
            { label: { cz: '3. Obnova účtu', en: '3. Restoring an account' }, text: {
              cz: 'Akcí pro obnovu v řádku koše vrátíte účet mezi aktivní se vším původním nastavením. Uživatel se může znovu přihlašovat.',
              en: 'The restore action in the trash row returns the account to the active ones with all its original settings. The user can sign in again.'
            } },
            { label: { cz: '4. Trvalé smazání', en: '4. Permanent deletion' }, text: {
              cz: 'Akcí pro trvalé smazání v koši účet odstraníte natrvalo (vyžaduje oprávnění mazat účty). Tento krok nelze vrátit.',
              en: 'The permanent delete action in the trash removes the account for good (requires the permission to delete accounts). This step cannot be undone.'
            } },
            { label: { cz: '5. Návrat k aktivním účtům', en: '5. Returning to active accounts' }, text: {
              cz: 'Stejnou položkou v nabídce akcí (její název se změní na zobrazení aktivních) se vrátíte zpět.',
              en: 'The same item in the action menu (its label changes to showing the active ones) takes you back.'
            } }
          ] },
          { type: 'grid', cards: [
            { title: { cz: 'Vlastní účet', en: 'Your own account' }, text: {
              cz: 'Účet, pod kterým jste právě přihlášeni, smazat nemůžete.',
              en: 'You cannot delete the account you are currently signed in with.'
            } },
            { title: { cz: 'Účty sysadmin', en: 'Sysadmin accounts' }, text: {
              cz: 'Účet s rolí sysadmin smí smazat jen jiný sysadmin. Při hromadném vyprázdnění koše zůstanou účty sysadmin v koši, pokud koš nevyprazdňuje sysadmin.',
              en: 'An account with the sysadmin role may be deleted only by another sysadmin. When the trash is emptied in bulk, sysadmin accounts stay in the trash unless a sysadmin is emptying it.'
            } },
            { title: { cz: 'E-mail účtu v koši je obsazený', en: 'The e-mail of a trashed account is taken' }, text: {
              cz: 'Dokud účet leží v koši, nelze založit nový účet se stejným e-mailem. Buď účet z koše obnovte, nebo ho nejprve trvale smažte.',
              en: 'While an account lies in the trash, a new account with the same e-mail cannot be created. Either restore the account from the trash, or permanently delete it first.'
            } },
            { title: { cz: 'Blokovat, nebo smazat?', en: 'Block or delete?' }, text: {
              cz: 'Pokud se uživatel může vrátit nebo si nejste jistí, účet zablokujte. Smazání používejte, když účet už potřeba nebude.',
              en: 'If the user may come back or you are not sure, block the account. Use deletion when the account will no longer be needed.'
            } }
          ] }
        ]
      },

      // ── 16 ──────────────────────────────────────────────────────────────
      {
        heading: { cz: '16. Povolené e-mailové domény (jen sysadmin)', en: '16. Allowed E-mail Domains (Sysadmin Only)' },
        blocks: [
          { type: 'text', content: {
            cz: 'Sysadmin může určit, s jakými e-mailovými adresami smějí vznikat nové účty - typicky jen s firemní doménou. Nastavení otevřete položkou pro e-mailové domény v nabídce akcí; tuto položku vidí pouze sysadmin.',
            en: 'A sysadmin can define which e-mail addresses new accounts may be created with - typically only the company domain. Open the settings with the e-mail domains item in the action menu; only a sysadmin sees this item.'
          } },
          { type: 'grid', cards: [
            { title: { cz: 'Hlavní doména', en: 'Primary domain' }, text: {
              cz: 'Základní firemní doména, například firma.cz. Jakmile je vyplněná, účty lze zakládat a přihlašovat se jen s adresami z této domény nebo z výjimek níže - platí pro všechny role včetně sysadmina.',
              en: 'The basic company domain, for example company.com. Once filled in, accounts can be created and can log in only with addresses from this domain or from the exceptions below - for every role, sysadmin included.'
            } },
            { title: { cz: 'Bez omezení', en: 'No restriction' }, text: {
              cz: 'Pokud hlavní doménu necháte prázdnou a uložíte, omezení se vypne a účet lze založit s jakýmkoli e-mailem.',
              en: 'If you leave the primary domain empty and save, the restriction is turned off and an account can be created with any e-mail.'
            } },
            { title: { cz: 'Výjimka pro doménu', en: 'Domain exception' }, text: {
              cz: 'Další celá doména, se kterou smějí účty vznikat - například doména partnerské firmy.',
              en: 'Another whole domain accounts may be created with - for example the domain of a partner company.'
            } },
            { title: { cz: 'Výjimka pro e-mail', en: 'E-mail exception' }, text: {
              cz: 'Jedna konkrétní adresa mimo povolené domény - například externí spolupracovník se soukromým e-mailem.',
              en: 'One specific address outside the allowed domains - for example an external collaborator with a private e-mail.'
            } }
          ] },
          { type: 'flow', steps: [
            { label: { cz: '1. Nastavení hlavní domény', en: '1. Setting the primary domain' }, text: {
              cz: 'Do pole hlavní domény napište doménu a klikněte na tlačítko pro uložení vedle pole. Systém uložení potvrdí. Hlavní doména se ukládá jen tímto tlačítkem.',
              en: 'Type the domain into the primary domain field and click the save button next to the field. The system confirms the save. The primary domain is saved only with this button.'
            } },
            { label: { cz: '2. Přidání výjimky', en: '2. Adding an exception' }, text: {
              cz: 'V části pro přidání výjimky zvolte typ (doména, nebo e-mail), napište hodnotu a klikněte na tlačítko pro přidání nebo stiskněte Enter. Výjimka se uloží okamžitě a objeví se v příslušném seznamu. Hodnoty zadávejte malými písmeny.',
              en: 'In the add-exception part choose the type (domain or e-mail), type the value, and click the add button or press Enter. The exception is saved immediately and appears in the corresponding list. Enter values in lower case.'
            } },
            { label: { cz: '3. Kontrola seznamů', en: '3. Checking the lists' }, text: {
              cz: 'Okno ukazuje dva seznamy: povolené domény a povolené e-maily. Prázdný seznam je označen textem, že v něm zatím nic není.',
              en: 'The window shows two lists: allowed domains and allowed e-mails. An empty list is marked with a text saying nothing is in it yet.'
            } },
            { label: { cz: '4. Odebrání výjimky', en: '4. Removing an exception' }, text: {
              cz: 'Křížkem u položky výjimku odeberete. Odebrání platí okamžitě: účty, které tím přestanou být povolené, jsou hned odhlášené a už se nepřihlásí - týká se to všech rolí, i sysadmina. Změnu, která by zablokovala vás samotné, systém neuloží; nejdřív si přidejte výjimku pro svůj e-mail.',
              en: 'The cross next to an item removes the exception. The removal applies immediately: accounts that are no longer allowed are logged out at once and cannot log in - this applies to every role, sysadmin included. A change that would block you yourself is not saved; add an exception for your own e-mail first.'
            } },
            { label: { cz: '5. Zavření okna', en: '5. Closing the window' }, text: {
              cz: 'Okno zavřete tlačítkem pro zavření, křížkem v rohu nebo kliknutím mimo okno. Během ukládání hlavní domény okno zavřít nelze.',
              en: 'Close the window with the close button, the cross in the corner, or by clicking outside the window. The window cannot be closed while the primary domain is being saved.'
            } }
          ] },
          { type: 'alert', variant: 'info', content: {
            cz: 'Omezení platí jen pro zakládání nových účtů. Existující účty zůstávají beze změny, i když jejich e-mail povoleným doménám neodpovídá, a omezení se nekontroluje ani při úpravě e-mailu existujícího účtu. Pokus o založení účtu s nepovolenou adresou systém odmítne a zaznamená jako bezpečnostní událost.',
            en: 'The restriction applies only to creating new accounts. Existing accounts stay unchanged even if their e-mail does not match the allowed domains, and the restriction is not checked when the e-mail of an existing account is edited either. An attempt to create an account with a disallowed address is refused and recorded as a security event.'
          } }
        ]
      },

      // ── 17 ──────────────────────────────────────────────────────────────
      {
        heading: { cz: '17. Pevná pravidla, která nelze obejít', en: '17. Fixed Rules That Cannot Be Bypassed' },
        blocks: [
          { type: 'text', content: {
            cz: 'Následující pravidla chrání systém před chybou i zneužitím. Platí vždy, bez ohledu na oprávnění, a nejsou chybou aplikace.',
            en: 'The following rules protect the system against mistakes and misuse. They always apply, regardless of permissions, and are not an application error.'
          } },
          { type: 'grid', cards: [
            { title: { cz: 'Účty sysadmin spravuje jen sysadmin', en: 'Sysadmin accounts are managed only by a sysadmin' }, text: {
              cz: 'Založení, úprava, povýšení na sysadmina, změna hesla cizího účtu sysadmin i jeho smazání jsou vyhrazeny roli sysadmin.',
              en: 'Creating, editing, promoting to sysadmin, changing the password of someone else with the sysadmin role, and deleting such an account are reserved for the sysadmin role.'
            } },
            { title: { cz: 'Sysadmin má vždy dvoufázové ověření', en: 'A sysadmin always has two-factor authentication' }, text: {
              cz: 'U role sysadmin nelze ověření vypnout.',
              en: 'The verification cannot be turned off for the sysadmin role.'
            } },
            { title: { cz: 'Sysadmina nelze zablokovat', en: 'A sysadmin cannot be blocked' }, text: {
              cz: 'Účet s rolí sysadmin nezablokuje nikdo, ani jiný sysadmin.',
              en: 'Nobody can block an account with the sysadmin role, not even another sysadmin.'
            } },
            { title: { cz: 'Sám sebe nezablokujete ani nesmažete', en: 'You cannot block or delete yourself' }, text: {
              cz: 'Vlastní účet nelze zablokovat ani smazat a vlastní roli si nelze změnit.',
              en: 'Your own account cannot be blocked or deleted, and you cannot change your own role.'
            } },
            { title: { cz: 'Nikdo nerozdá víc, než sám má', en: 'Nobody gives away more than they have' }, text: {
              cz: 'Roli ani oprávnění navíc nelze přidělit, pokud by tím cílový účet získal oprávnění, které sami nemáte. Výjimkou je sysadmin.',
              en: 'A role or an extra permission cannot be assigned if the target account would gain a permission you do not have yourself. The sysadmin is the exception.'
            } },
            { title: { cz: 'Jeden e-mail, jeden účet', en: 'One e-mail, one account' }, text: {
              cz: 'Dva účty se stejným e-mailem existovat nemohou, a to včetně účtů v koši.',
              en: 'Two accounts with the same e-mail cannot exist, including accounts in the trash.'
            } },
            { title: { cz: 'Vše se zaznamenává', en: 'Everything is recorded' }, text: {
              cz: 'Založení, úpravy, změny hesel, blokace, mazání, obnovy i odmítnuté pokusy se ukládají do záznamů systému včetně toho, kdo akci provedl.',
              en: 'Creations, edits, password changes, blocks, deletions, restores, and refused attempts are stored in the system records, including who performed the action.'
            } }
          ] }
        ]
      },

      // ── 18 ──────────────────────────────────────────────────────────────
      {
        heading: { cz: '18. Co dělat, když...', en: '18. What to Do When...' },
        blocks: [
          { type: 'grid', cards: [
            { title: { cz: 'Novému uživateli nepřišel aktivační e-mail', en: 'A new user did not receive the activation e-mail' }, text: {
              cz: 'Nechte zkontrolovat nevyžádanou poštu, ověřte správnost e-mailu v účtu a odešlete aktivaci znovu (kapitola 06).',
              en: 'Have the spam folder checked, verify the e-mail in the account is correct, and resend the activation (chapter 06).'
            } },
            { title: { cz: 'Aktivační odkaz nefunguje', en: 'The activation link does not work' }, text: {
              cz: 'Odkaz vypršel nebo už byl použit. Odešlete aktivaci znovu a upozorněte uživatele, ať použije nejnovější e-mail.',
              en: 'The link has expired or has already been used. Resend the activation and tell the user to use the newest e-mail.'
            } },
            { title: { cz: 'Uživatel zapomněl heslo', en: 'A user forgot the password' }, text: {
              cz: 'Odkažte ho na odkaz pro zapomenuté heslo na přihlašovací stránce. Až když to nejde, změňte heslo sami (kapitola 11).',
              en: 'Point them to the forgotten-password link on the sign-in page. Only if that is not possible, change the password yourself (chapter 11).'
            } },
            { title: { cz: 'Uživateli nechodí ověřovací kód', en: 'A user is not receiving the verification code' }, text: {
              cz: 'Nechte zkontrolovat nevyžádanou poštu a po 60 sekundách vyžádat kód znovu. Pokud ověření není vynucené, lze ho v úpravě účtu dočasně vypnout.',
              en: 'Have the spam folder checked and the code requested again after 60 seconds. If the verification is not forced, it can be turned off temporarily by editing the account.'
            } },
            { title: { cz: 'Podezření na zneužití účtu', en: 'Suspected misuse of an account' }, text: {
              cz: 'Účet ihned zablokujte - uživatel bude odhlášen všude. Poté změňte heslo, situaci prověřte a teprve pak účet odblokujte.',
              en: 'Block the account immediately - the user is signed out everywhere. Then change the password, investigate the situation, and only then unblock the account.'
            } },
            { title: { cz: 'Uživatel ve firmě končí', en: 'A user is leaving the company' }, text: {
              cz: 'Účet zablokujte nebo smažte do koše v den odchodu. Jakmile je jisté, že účet už nebude potřeba, smažte ho z koše trvale.',
              en: 'Block the account or delete it to the trash on the day of departure. Once it is certain the account will not be needed again, delete it from the trash permanently.'
            } },
            { title: { cz: 'Nevidím tlačítko nebo položku nabídky', en: 'I cannot see a button or menu item' }, text: {
              cz: 'Chybí vám příslušné oprávnění (kapitola 01), nebo akce pro daný účet nedává smysl - například odeslání aktivace u aktivovaného účtu.',
              en: 'You lack the relevant permission (chapter 01), or the action makes no sense for the account - for example resending the activation for an activated account.'
            } },
            { title: { cz: 'V seznamu chybí role', en: 'A role is missing from the list' }, text: {
              cz: 'Role obsahuje oprávnění, které sami nemáte, takže ji přidělit nesmíte. Požádejte sysadmina.',
              en: 'The role contains a permission you do not have yourself, so you may not assign it. Ask a sysadmin.'
            } },
            { title: { cz: 'Účet nejde založit kvůli doméně', en: 'The account cannot be created because of the domain' }, text: {
              cz: 'E-mail nespadá pod povolené domény. Požádejte sysadmina o výjimku pro doménu nebo pro konkrétní e-mail (kapitola 16).',
              en: 'The e-mail does not belong to the allowed domains. Ask a sysadmin for a domain exception or an exception for the specific e-mail (chapter 16).'
            } },
            { title: { cz: 'Účet s tímto e-mailem už existuje', en: 'An account with this e-mail already exists' }, text: {
              cz: 'Vyhledejte účet filtrem podle e-mailu mezi aktivními účty. Pokud tam není, podívejte se do koše - účet buď obnovte, nebo trvale smažte.',
              en: 'Look the account up with the e-mail filter among the active accounts. If it is not there, check the trash - either restore the account or delete it permanently.'
            } },
            { title: { cz: 'Pole ve formuláři nejde změnit', en: 'A field in the form cannot be changed' }, text: {
              cz: 'Pole je uzamčené pravidlem: dvoufázové ověření u vynucených účtů, blokace u účtů sysadmin, oprávnění obsažená v roli.',
              en: 'The field is locked by a rule: two-factor authentication on forced accounts, blocking on sysadmin accounts, permissions contained in the role.'
            } },
            { title: { cz: 'Zobrazila se chyba, které nerozumím', en: 'An error appeared that I do not understand' }, text: {
              cz: 'Zkuste akci zopakovat. Pokud chyba trvá, nahlaste ji přes formulář podpory a popište, co jste dělali a u kterého účtu.',
              en: 'Try the action again. If the error persists, report it through the support form and describe what you were doing and with which account.'
            } }
          ] }
        ]
      },

      // ── Conclusion ───────────────────────────────────────────────────────────
      {
        blocks: [
          { type: 'note', highlight: true, content: {
            cz: 'Slovo závěrem: účty obsahují osobní údaje a otevírají přístup do celé administrace. Zakládejte je jen lidem, kteří je opravdu potřebují, přidělujte nejnižší roli, která k práci stačí, nepotřebné účty blokujte nebo mažte a hesla ani ověřovací kódy nikdy nesdílejte.',
            en: 'A final word: accounts contain personal data and open access to the whole administration. Create them only for people who really need them, assign the lowest role that is sufficient for the work, block or delete accounts that are no longer needed, and never share passwords or verification codes.'
          } }
        ]
      }
    ]
  },
  {
    id: 'core-logs',
    navGroup: 'core',
    navLabel: { cz: 'Systémové logy', en: 'System Logs' },
    navOrder: 23,
    header: { cz: 'Core - Systémové logy', en: 'Core - System Logs' },
    devNote: "CoreLogsComponent, route 'core/logs', permission 'view-core'. Poznámka v routing komentáři: dočasně čte ze stejného zdroje jako web/business-logs.",
    sections: [ { blocks: [ { type: 'lead', content: {
      cz: 'Testovací obsah - přehled systémových auditních logů.',
      en: 'Placeholder content - overview of system audit logs.'
    } } ] } ]
  },
  {
    id: 'security-events',
    navGroup: 'core',
    navLabel: { cz: 'Bezpečnostní monitoring', en: 'Security Monitoring' },
    navOrder: 24,
    header: { cz: 'Bezpečnostní monitoring', en: 'Security Monitoring' },
    devNote: "SecurityEventsComponent, route 'core/security-events', permission 'core-security-view'. Triage podezřelých eventů, retenční politika (GDPR), ruční purge.",
    sections: [ { blocks: [ { type: 'lead', content: {
      cz: 'Testovací obsah - monitoring podezřelé aktivity, triage eventů a nastavení retenční doby.',
      en: 'Placeholder content - monitoring of suspicious activity, event triage, and retention period settings.'
    } } ] } ]
  },

  // ── Shop (matches the 'shop/*' routes of admin-routing.module.ts) ────────────

  {
    id: 'shop-dashboard',
    navGroup: 'shop',
    navLabel: { cz: 'Dashboard', en: 'Dashboard' },
    navOrder: 25,
    header: { cz: 'Shop - Dashboard', en: 'Shop - Dashboard' },
    devNote: "ShopDashboardComponent, route 'shop/dashboard', permission 'shop-view-dashboard'.",
    sections: [ { blocks: [ { type: 'lead', content: {
      cz: 'Testovací obsah - přehledová stránka e-shop modulu administrace.',
      en: 'Placeholder content - the overview page of the Shop admin module.'
    } } ] } ]
  },
  {
    id: 'shop-products',
    navGroup: 'shop',
    navLabel: { cz: 'Produkty', en: 'Products' },
    navOrder: 26,
    header: { cz: 'Správa produktů', en: 'Product Management' },
    devNote: "ProductsComponent, route 'shop/products', permission 'shop-products-view'. Zahrnuje varianty a obrázky produktu (samostatné modaly).",
    sections: [ { blocks: [ { type: 'lead', content: {
      cz: 'Testovací obsah - správa produktového katalogu, variant a obrázků.',
      en: 'Placeholder content - management of the product catalog, variants, and images.'
    } } ] } ]
  },
  {
    id: 'shop-categories',
    navGroup: 'shop',
    navLabel: { cz: 'Kategorie', en: 'Categories' },
    navOrder: 27,
    header: { cz: 'Správa kategorií', en: 'Category Management' },
    devNote: "CategoriesComponent, route 'shop/categories', permission 'shop-categories-view'. Stromová struktura kategorií + přiřazování produktů.",
    sections: [ { blocks: [ { type: 'lead', content: {
      cz: 'Testovací obsah - hierarchická správa kategorií produktů.',
      en: 'Placeholder content - hierarchical management of product categories.'
    } } ] } ]
  },
  {
    id: 'shop-orders',
    navGroup: 'shop',
    navLabel: { cz: 'Objednávky', en: 'Orders' },
    navOrder: 28,
    header: { cz: 'Správa objednávek', en: 'Order Management' },
    devNote: "OrdersComponent, route 'shop/orders', permission 'shop-orders-view'.",
    sections: [ { blocks: [ { type: 'lead', content: {
      cz: 'Testovací obsah - správa e-shopových objednávek, stavů a plateb.',
      en: 'Placeholder content - management of e-shop orders, statuses, and payments.'
    } } ] } ]
  },
  {
    id: 'shop-customers',
    navGroup: 'shop',
    navLabel: { cz: 'Zákazníci', en: 'Customers' },
    navOrder: 29,
    header: { cz: 'Správa zákazníků', en: 'Customer Management' },
    devNote: "CustomersComponent, route 'shop/customers', permission 'shop-customers-view'.",
    sections: [ { blocks: [ { type: 'lead', content: {
      cz: 'Testovací obsah - správa zákaznických účtů a jejich historie objednávek.',
      en: 'Placeholder content - management of customer accounts and their order history.'
    } } ] } ]
  },
  {
    id: 'shop-shipping-methods',
    navGroup: 'shop',
    navLabel: { cz: 'Způsoby dopravy', en: 'Shipping Methods' },
    navOrder: 30,
    header: { cz: 'Způsoby dopravy', en: 'Shipping Methods' },
    devNote: "ShippingMethodsComponent, route 'shop/shipping-methods', permission 'shop-shipping-methods-view'.",
    sections: [ { blocks: [ { type: 'lead', content: {
      cz: 'Testovací obsah - správa dostupných způsobů dopravy.',
      en: 'Placeholder content - management of available shipping methods.'
    } } ] } ]
  },
  {
    id: 'shop-payment-methods',
    navGroup: 'shop',
    navLabel: { cz: 'Platební metody', en: 'Payment Methods' },
    navOrder: 31,
    header: { cz: 'Platební metody', en: 'Payment Methods' },
    devNote: "PaymentMethodsComponent, route 'shop/payment-methods', permission 'shop-payment-methods-view'.",
    sections: [ { blocks: [ { type: 'lead', content: {
      cz: 'Testovací obsah - správa dostupných platebních metod.',
      en: 'Placeholder content - management of available payment methods.'
    } } ] } ]
  },
  {
    id: 'shop-suppliers',
    navGroup: 'shop',
    navLabel: { cz: 'Dodavatelé', en: 'Suppliers' },
    navOrder: 32,
    header: { cz: 'Správa dodavatelů', en: 'Supplier Management' },
    devNote: "SuppliersComponent, route 'shop/suppliers', permission 'shop-suppliers-view'.",
    sections: [ { blocks: [ { type: 'lead', content: {
      cz: 'Testovací obsah - evidence dodavatelů produktů.',
      en: 'Placeholder content - tracking of product suppliers.'
    } } ] } ]
  },
  {
    id: 'coupons',
    navGroup: 'shop',
    navLabel: { cz: 'Slevové kupóny', en: 'Discount Coupons' },
    navOrder: 33,
    header: { cz: 'Slevové kupóny', en: 'Discount Coupons' },
    devNote: "CouponsComponent, route 'shop/coupons', permission 'shop-coupons-view'.",
    sections: [ { blocks: [ { type: 'lead', content: {
      cz: 'Testovací obsah - správa slevových kupónů a jejich podmínek.',
      en: 'Placeholder content - management of discount coupons and their conditions.'
    } } ] } ]
  },
  {
    id: 'shop-logs',
    navGroup: 'shop',
    navLabel: { cz: 'Logy', en: 'Logs' },
    navOrder: 34,
    header: { cz: 'Shop - Logy', en: 'Shop - Logs' },
    devNote: "ShopLogsComponent, route 'shop/logs', permission 'shop-view-logs'.",
    sections: [ { blocks: [ { type: 'lead', content: {
      cz: 'Testovací obsah - auditní log akcí provedených v e-shop modulu.',
      en: 'Placeholder content - an audit log of actions performed in the Shop module.'
    } } ] } ]
  },
  {
    id: 'edit-eshop',
    navGroup: 'shop',
    navLabel: { cz: 'Nastavení e-shopu', en: 'E-shop Settings' },
    navOrder: 35,
    header: { cz: 'Globální nastavení e-shopu', en: 'Global E-shop Settings' },
    devNote: "EditEshopComponent, route 'shop/edit-eshop', permission 'shop-edit-eshop-view'.",
    sections: [ { blocks: [ { type: 'lead', content: {
      cz: 'Testovací obsah - globální nastavení e-shopu.',
      en: 'Placeholder content - global e-shop settings.'
    } } ] } ]
  },
];