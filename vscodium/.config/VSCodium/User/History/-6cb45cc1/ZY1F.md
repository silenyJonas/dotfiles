# VT.md – audit web-platform (2026-10-31)

Stav: větev `main` @ `c285a61` + patch 0019 (úklid komentářů).
Rozsah: hlavně **core** a **web** (API + ERP). U **shopu** jsou jen nálezy, které můžou být kritické.
Závažnost: 🔴 Critical · 🟠 High · 🟡 Medium · 🔵 Low · ⚪ Cosmetic / Info

## Přehled

| ID | Závažnost | Oblast | Nález |
|----|-----------|--------|-------|
| done VT-01 | 🔴 | ERP / deploy | Produkční build používá vývojový `environment.ts` |
| done VT-02 | 🟠 | API / upload | Uložené XSS přes přílohy (SVG/HTML se servíruje inline ze stejného originu) |
| VT-03 | 🟠 | Auth | Access token i 7denní refresh token leží v `sessionStorage` |
| VT-04 | 🟠 | Server | Chybí bezpečnostní HTTP hlavičky (CSP, HSTS, frame-ancestors, nosniff…) |
| VT-05 | 🟡 | API | CORS `*` + `supports_credentials: true` vrací zpět libovolný origin |
| VT-06 | 🟡 | Web / formuláře | Veřejné formuláře nemají captchu: spam, rozesílání e-mailů, zaplnění disku |
| VT-07 | 🟡 | Auth / logika | Jedna relace na uživatele, refresh smaže všechny tokeny, `/refresh` nemá throttle |
| VT-08 | 🟡 | Admin / projekty | Heslo k portálu projektu v čitelné podobě v `sessionStorage` |
| VT-09 | 🟡 | Konfigurace | Nebezpečné výchozí hodnoty (`SESSION_SECURE_COOKIE=false`, `APP_DEBUG=true`) |
| VT-10 | 🟡 | GDPR | Chybí retence: CV, poptávky, objednávky, leady, tickety; lead token nikdy neexpiruje |
| VT-11 | 🟡 | GDPR | Google Fonts se načítají z Googlu před souhlasem |
| VT-12 | 🟡 | GDPR | Souhlas s cookies se neeviduje na serveru |
| VT-13 | 🟡 | Logika / práva | Změna vlastního hesla a 2FA vyžaduje oprávnění `web-view-personal-info` |
| VT-14 | 🟡 | UI / API | „Smazat vybrané“ je vidět i u tabulek bez `bulk-delete` endpointu (404) |
| VT-15 | 🟡 | i18n / UX | Potvrzení objednávky a stránka údržby jsou natvrdo česky |
| VT-16 | 🔵 | Shop | `simulate-payment` je zapnutý všude mimo `APP_ENV=production` a bere libovolné `order_id` |
| VT-17 | 🔵 | API | Veřejný lead endpoint vrací interní `id` a nemá vlastní throttle |
| done VT-18 | 🔵 | API | `Content-Disposition` se skládá přes `addslashes` |
| VT-19 | 🔵 | SEO / branding | JSON-LD, canonical a og:* jsou natvrdo nastavené na RPSW / rpsw.cz |
| VT-20 | ⚪ | Kód | Duplicitní kód (log controllery, dashboardy, seznamy přípon) |
| VT-21 | ⚪ | Kód | Mrtvý kód a zbytky (`move.sh`, falešná `/sanctum/csrf-cookie`, `closeThread()`, nepoužitá práva) |
| VT-22 | ⚪ | Dokumentace | Česká nebo zastaralá dokumentace a české názvy testů |

---

## 🔴 VT-01 – Produkční build používá vývojový environment

- **Problém:** `angular.json` nemá v konfiguraci `production` žádné `fileReplacements`, takže `ng build --configuration production` (volá ho `deploy/build.sh`) zabalí `environment.ts`. V něm je:
  - `base_api_url: 'http://127.0.0.1:8000/api'`
  - testovací Turnstile klíč `1x00000000000000000000AA`

  Navíc `environment.prod.ts` nemá `public_storage_url`. Používá ho `web-settings.component.ts` pro náhled loga a ikon.
- **Proč to vadí:**
  - Pokud se před buildem soubor ručně nepřepíše, produkce volá localhost a admin ani web nefungují.
  - Testovací site key vrací tokeny, které produkční secret odmítne. Po 3 špatných pokusech je tedy přihlášení k danému účtu fakticky zamčené.
  - V adminu se nezobrazuje logo.
- **Oprava:**
  - Do `configurations.production` přidat `fileReplacements` (`environment.ts` → `environment.prod.ts`).
  - Do prod souboru doplnit `public_storage_url: '/storage'` a skutečný Turnstile site key (nejlépe ho dosazovat při buildu, ne commitovat).
  - Do `deploy/build.sh` přidat kontrolu, že výsledný bundle neobsahuje `127.0.0.1`.

## 🟠 VT-02 – Uložené XSS přes přílohy

- **Problém:** Tyto přílohy nahrává zákazník a admin je otevírá přes `attachments/view` (`AttachmentDownloadController::view()`). Ten je vrací `inline` s MIME typem odvozeným ze souboru:
  - přílohy vláken portálu: `StoreProjectThreadMessageRequest` a `StoreProjectThreadRequest` výslovně povolují `svg`;
  - poptávky a objednávky: `ValidatesAttachmentSecurity` používá **blacklist**, takže projde `.html`, `.htm`, `.svg`, `.xml`, `.xhtml`.

  V produkci běží API na stejném originu (`/api`, viz `deploy/server/.htaccess`). Chybí `X-Content-Type-Options: nosniff` a CSP.
- **Proč to vadí:** JavaScript v SVG nebo HTML se spustí na originu administrace. Může číst `localStorage` (relace portálu, košík), podvrhnout přihlašovací formulář na důvěryhodné doméně a volat API. Spolu s VT-03 hrozí převzetí účtu.
- **Oprava:**
  - Všude přejít na **whitelist** a z povolených přípon vyřadit `svg`.
  - `view` povolit jen pro `pdf` a rastrové obrázky (`jpg`, `png`, `webp`, `gif`), vše ostatní posílat jako `attachment`.
  - Na obě odpovědi přidat `X-Content-Type-Options: nosniff` a `Content-Security-Policy: sandbox; default-src 'none'`.
  - Ideálně přílohy servírovat z oddělené (cookieless) domény.

## 🟠 VT-03 – Tokeny v sessionStorage místo cookies

- **Problém:** `AuthService.persistSession()` ukládá do `sessionStorage` tyto hodnoty:
  - `accessToken` (60 min)
  - `refreshToken` (7 dní, rotuje se)
  - `userId`, `userEmail`, `userRole`, `userPermissions`

  Portál projektu ukládá `session_token` (24 h) do `localStorage`.
- **Proč to vadí:** Jakékoli XSS (např. VT-02 nebo knihovna třetí strany) může refresh token přečíst a držet se v účtu až 7 dní, i po zavření záložky. Role a oprávnění v úložišti jdou snadno přepsat. API je sice vynucuje, ale UI pak působí nekonzistentně.
- **Oprava:** API je ve stejném originu, takže lze použít **Sanctum SPA (stateful) autentizaci**:
  - session cookie s `HttpOnly`, `Secure` a `SameSite=Lax/Strict`;
  - `XSRF-TOKEN` (Angular `withXsrfConfiguration`);
  - žádný token v JS.

  Alternativa: refresh token v `HttpOnly; Secure; SameSite=Strict; Path=/api/refresh` cookie a access token jen v paměti. Pro portál totéž (cookie s `Path=/api/projects/public`). Předpoklad: nejdřív opravit VT-05.

## 🟠 VT-04 – Chybí bezpečnostní HTTP hlavičky

- **Problém:** V `.htaccess` ani v middleware nejsou:
  - `Content-Security-Policy`
  - `Strict-Transport-Security`
  - `X-Frame-Options` / `frame-ancestors`
  - `X-Content-Type-Options`
  - `Referrer-Policy`
  - `Permissions-Policy`
- **Proč to vadí:** Admin jde vložit do iframe (clickjacking), XSS nic neomezuje a není vynucené HTTPS.
- **Oprava:** Middleware `SecurityHeaders` pro API a `Header always set …` v `deploy/server/.htaccess` pro SPA. CSP začít v režimu `Report-Only` a povolit jen Turnstile a GA domény.

## 🟡 VT-05 – CORS reflektuje libovolný origin

- **Problém:** `config/cors.php` má `allowed_origins => ['*']` a zároveň `supports_credentials => true`. Knihovna `php-cors` v této kombinaci vrací do `Access-Control-Allow-Origin` origin z požadavku a přidává `Allow-Credentials: true`.
- **Proč to vadí:** Dnes to tlumí jen to, že se používá Bearer token. Po přechodu na cookies (VT-03) by se z toho stalo plnohodnotné CSRF a čtení dat z cizích webů.
- **Oprava:** Seznam originů brát z `.env` (`FRONTEND_URL`, `CORS_ALLOWED_ORIGINS`). `supports_credentials` zapnout jen pro cookie autentizaci. V produkci, kde vše běží ve stejném originu, CORS skoro nepotřebujeme.

## 🟡 VT-06 – Veřejné formuláře bez captchy

- **Problém:** `raw_request_commissions`, `sales_orders` a `job_applications` mají limit jen `throttle:10,1` na IP. Každý požadavek může nést až 10 souborů po 20 MB (u CV 20 MB) a odeslat potvrzovací e-mail na **libovolnou zadanou adresu**.
- **Proč to vadí:**
  - Z jedné IP jde až 14 400 požadavků denně, tedy terabajty na disku.
  - Server se dá zneužít k rozesílání e-mailů cizím lidem: hrozí poškození reputace domény a blacklist.
  - Databázi zaplní spam.
- **Oprava:**
  - Turnstile na všechny veřejné formuláře (služba už existuje).
  - Denní kvóta na IP a na e-mail příjemce.
  - Nižší limity souborů.
  - Ukládat do kvóty disku a mazat neaktivní soubory.

## 🟡 VT-07 – Relace a refresh tokeny

- **Problém:**
  - `issueTokens()` smaže všechny refresh tokeny uživatele a `refresh()` smaže **všechny** jeho access tokeny (`$user->tokens()->delete()`).
  - Refresh token nemá detekci znovupoužití (rodiny tokenů).
  - `/refresh` nemá žádný throttle.
- **Proč to vadí:**
  - Druhé přihlášení (jiná záložka nebo zařízení) odhlásí to první, nejpozději při dalším refreshi (timer 20 min). Uživatel přijde o rozpracovaný formulář.
  - Ukradený refresh token se nedá odhalit.
  - Endpoint se dá zahltit.
- **Oprava:**
  - Refresh token vázat na zařízení (`device_id`, rodina) a při refreshi mazat jen access token té relace.
  - Při použití už rotovaného tokenu zneplatnit celou rodinu a zapsat bezpečnostní událost.
  - `throttle:30,1` na `/refresh`.
  - Pokud je jedna relace záměr, napsat to do dokumentace i do UI (hláška „přihlášen jinde“).

## 🟡 VT-08 – Heslo portálu v sessionStorage

- **Problém:** `ProjectsComponent.storeRevealedPassword()` ukládá vygenerované heslo k portálu projektu v čitelné podobě do `sessionStorage` (`rpsw_project_pw_<id>`).
- **Proč to vadí:** Heslo, které se má ukázat jen jednou, zůstává v úložišti přístupném z JS. Přečte ho každé XSS i cokoli dalšího v dané záložce.
- **Oprava:** Držet heslo jen v proměnné komponenty. Po zavření modalu ho nejde znovu zobrazit, jen přegenerovat. Dál se nikam neukládá.

## 🟡 VT-09 – Nebezpečné výchozí hodnoty konfigurace

- **Problém:**
  - `config/session.php` má `'secure' => env('SESSION_SECURE_COOKIE', false)`.
  - `.env.example` má `APP_DEBUG=true`.
  - `deploy/server/configure-server.sh` produkční hodnoty jen připomene přes `echo`.
- **Proč to vadí:** Jediná zapomenutá proměnná znamená únik stack trace a `.env` hodnot (debug stránka) nebo session cookie přes HTTP.
- **Oprava:**
  - Výchozí `secure` nastavit na `env('APP_ENV') === 'production'`.
  - Při startu v produkci kontrolovat (`AppServiceProvider::boot`) `APP_DEBUG=false`, `APP_KEY`, HTTPS a hodnotu `SESSION_SECURE_COOKIE`.
  - Setup skript ať tyto hodnoty rovnou zapíše.

## 🟡 VT-10 – Retence osobních údajů (GDPR čl. 5 odst. 1 písm. e)

- **Problém:** Plánovač (`routes/console.php`) maže jen `core_security_events` a importní dávky. CV uchazečů, poptávky, objednávky, leady, tickety i data portálu zůstávají navždy. `web_sales_leads.public_token` nemá expiraci: odkaz s osobními údaji platí, dokud ho někdo nepoužije.
- **Proč to vadí:** Porušuje se zásada omezení uložení. U CV je běžná lhůta 6–12 měsíců (bez souhlasu s delší evidencí). Přeposlaný odkaz na leadu prozradí osobní údaje.
- **Oprava:**
  - Retenční nastavení pro každou entitu (vzor `CoreSecuritySetting`) a denní příkaz `Purge…`, který maže nebo anonymizuje záznamy i soubory.
  - `public_token_expires_at` (např. 30 dní) s kontrolou v `showByToken()`.

## 🟡 VT-11 – Google Fonts před souhlasem

- **Problém:** `erp/src/index.html` načítá `fonts.googleapis.com` / `fonts.gstatic.com` hned při načtení stránky.
- **Proč to vadí:** IP adresa návštěvníka odchází Googlu bez právního základu. LG München I (3 O 17493/20) to označilo za porušení GDPR a hrozí za to žaloby.
- **Oprava:** Fonty hostovat lokálně (`@fontsource/*` nebo soubory v `assets/fonts`) a odstranit `preconnect`.

## 🟡 VT-12 – Souhlas s cookies se neeviduje

- **Problém:** `CookieConsentService` ukládá souhlas jen do `localStorage`.
- **Proč to vadí:** Podle čl. 7 odst. 1 GDPR musí správce souhlas umět doložit (verzi textu, čas a rozsah). Bez serverového záznamu to nejde.
- **Oprava:** V `save()` poslat na API anonymní záznam: náhodné `consent_id`, verze, kategorie, čas, hash IP. Uchovávat ho po omezenou dobu.

## 🟡 VT-13 – Vlastní profil závisí na oprávnění

- **Problém:** Routa `core/personal-info` (změna vlastního hesla, zapnutí 2FA) je chráněná `web-view-personal-info`. API je přitom pro vlastní účet otevřené přes `selfParam`.
- **Proč to vadí:** Role bez tohoto práva (např. nová „read-only shop“) si **nemůže změnit heslo ani nastavit 2FA**. Je to logická díra i bezpečnostní problém. Klíč má navíc prefix `web-`, ačkoli jde o core funkci.
- **Oprava:** Stránku zpřístupnit každému přihlášenému (bez permission guardu), případně ji udělat povinnou součástí každé role. Klíč přejmenovat na `core-…`.

## 🟡 VT-14 – Hromadné mazání bez backendu

- **Problém:** `TableBuilderComponent.canBulkDelete` zobrazí „Smazat vybrané“, kdykoli má tabulka `delete_button`. Endpoint `…/bulk-delete` ale chybí u:
  - shop: `products`, `customers`, `orders`, `coupons`, `shipping_methods`;
  - core: `security_events`.

  Vypnuté je to jen u administrátorů (`[bulkDeleteDisabled]="true"`).
- **Proč to vadí:** Uživatel vybere řádky, potvrdí smazání a dostane 404 s chybovou hláškou.
- **Oprava:** Na těchto stránkách nastavit `[bulkDeleteDisabled]="true"`, nebo doplnit `bulkDestroy()` podle vzoru ostatních controllerů (u objednávek pozor na vazby a sklad).

## 🟡 VT-15 – Natvrdo české texty pro zákazníka

- **Problém:**
  - `emails/web/sales-order-received.blade.php` má titulek i celé tělo napevno česky. Potvrzení poptávky (`raw-request-commission-received`) je přitom lokalizované přes `RawRequestEmailTemplate`.
  - `web-maintenance.component.html` je česky.
  - `api/scripts/setup-queue-cron.sh` vypisuje česká hlášení.
- **Proč to vadí:** Zahraniční zákazník dostane český e-mail. Je to nekonzistence mezi dvěma podobnými workflow.
- **Oprava:** Šablonu objednávky převést na stejný mechanismus jako poptávku (texty z `web_site_settings` + jazyk záznamu). Stránku údržby napojit na překlady (`maintenance.*`).

## 🔵 VT-16 – Simulace platby (shop)

- **Problém:** `ShopCheckoutController::simulatePayment()` je zapnutý, kdykoli `APP_ENV` není `production`, a bere libovolné sekvenční `order_id` bez vazby na zákazníka.
- **Proč to vadí:** Na stagingu nebo testu se skutečnými daty si kdokoli „zaplatí“ cizí objednávku. Kritické by bylo, kdyby se proměnná prostředí nastavila špatně.
- **Oprava:** Výchozí hodnota `false`, zapínat jen explicitně. Místo `order_id` chtít podepsaný jednorázový `payment_token`, který vrací `createOrder`.

## 🔵 VT-17 – Veřejný lead endpoint

- **Problém:** `GET public/sales-leads/{token}` vrací v odpovědi interní `id` (komentář v routách přitom říká, že se interní ID nemá používat) a nemá vlastní throttle.
- **Proč to vadí:** Jde o zbytečný únik interní informace a o neomezený endpoint s osobními údaji. Token má 40 znaků, takže uhodnout ho je nereálné.
- **Oprava:** `id` z odpovědi odstranit (formulář se váže přes token) a přidat `throttle:30,1`.

## 🔵 VT-18 – Content-Disposition přes addslashes

- **Problém:** `AttachmentDownloadController::view()` skládá `inline; filename="…"` ručně.
- **Proč to vadí:** Názvy s diakritikou nebo speciálními znaky se v prohlížečích rozbíjejí (chybí `filename*`).
- **Oprava:** Použít `HeaderUtils::makeDisposition('inline', $name, Str::ascii($name))`.

## 🔵 VT-19 – Natvrdo nastavené SEO a branding

- **Problém:**
  - `home.component.html` obsahuje JSON-LD s „RPSW“, `rpsw.cz` a českým popisem.
  - `index.html` má `canonical` a `og:*` na `rpsw.cz`.
  - Klíče v úložišti mají prefix `rpsw_*`.
  - Cron marker se jmenuje `rpsw-queue-worker`.
- **Proč to vadí:** Jiná instalace hlásí vyhledávačům cizí firmu a cizí canonical URL, což poškozuje SEO.
- **Oprava:** JSON-LD a meta tagy generovat ze `SiteSetting` (`Meta` / `Renderer2`). Prefixy přejmenovat neutrálně, ideálně s migrací starých klíčů.

## ⚪ VT-20 – Duplicity

- `CoreLogController`, `WebLogController` a `ShopLogController` mají skoro stejné `index()` (filtry, hledání, řazení). Lepší je trait nebo base třída `FiltersLogQuery`.
- Core a Web dashboard duplikují hero, srovnávací pruhy, `eventTypeLabel` mapy i ikony. Lepší je sdílená base komponenta nebo service.
- Seznam povolených přípon je zkopírovaný ve `Store`/`UpdateWebSupportTicketRequest`, v requestech uchazečů a v requestech portálu. Lepší je jedno místo, např. `config/uploads.php`.

## ⚪ VT-21 – Mrtvý kód a zbytky

- `erp/move.sh`: jednorázový skript na opravu `routerLink` z minulosti. Navrhuji smazat (před smazáním potvrdit).
- `Route::get('/sanctum/csrf-cookie', fn() => 204)`: falešná routa. Při přechodu na Sanctum SPA ji nahradit skutečnou, jinak smazat.
- `ProjectPortalComponent.closeThread()`: označená `@deprecated` a nepoužitá.
- Práva `view-web` a `view-eshop` jsou v seedu, ale nikde se nepoužívají.
- Popisy práv v `seeders/data/permissions.php` jsou česky. Admin je zobrazuje v jednom jazyce a modul u `core-view-welcome-page` je `web`.
- Factories (`UserFactory`, `BusinessLogFactory` – `user_login_id`, `RawRequestCommissionFactory`) neodpovídají aktuálnímu schématu. Ověřit a opravit, nebo smazat.

## ⚪ VT-22 – Dokumentace a testy

- `docs/development_guid.txt` je česky a zastaralý (XAMPP). `docs/tree.txt` je zastaralý (např. `TOTO_backlog_task_admin_domain.json`).
- `erp/src/app/admin/components/builders/enum-and-i18n-in-builder-components.md` a `erp/src/assets/i18n/admin/AdminI18N_doc.md` jsou česky.
- 143 českých názvů testů (`it('…')`, `describe('…')`) ve 4 spec souborech: `auth.service`, `auth-token.interceptor`, `loading.interceptor`, `entitiy-crud.service`. Ten poslední má navíc překlep v názvu souboru (`entitiy`).

---

### Ověřeno bez nálezu

- Klíče oprávnění: všechna `permission:*` v `api.php` i všechna `data.permission` v `admin-routing.module.ts` existují v seedu. Mezi API a ERP jsem nenašel nesoulad.
- Captcha je fail-closed. 2FA má limit pokusů i resendů. Refresh i aktivační tokeny se v DB ukládají jako hash.
- Hesla portálu se ukládají jako hash a sezení portálu jako SHA-256. Přílohy jsou na privátním disku a stahují se přes podepsané URL.
- `bypassSecurityTrustHtml` se používá jen pro statické SVG ikony. Ostatní `[innerHTML]` prochází sanitizací Angularu.
