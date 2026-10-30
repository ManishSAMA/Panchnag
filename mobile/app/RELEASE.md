# Releasing to Google Play

How to build a signed bundle and get it onto the Play Console internal testing
track. Release builds are signed and uploaded by hand; CI only checks that the
bundle builds and never signs (plan: `python_engine/python_engine/plans/mobile-app-flutter.md` §1a).

## 1. The upload key (once)

Play App Signing holds the real app-signing key. You sign uploads with an
**upload key** that only you have. If it is lost, Play support can reset it,
but keep it safe anyway: store the keystore and its password in your password
manager, plus one offline backup. Never put either in the repo.

Create the keystore **outside the repo**. `keytool` ships with Android Studio's
JDK (`C:\Program Files\Android\Android Studio\jbr\bin\keytool.exe`). In
PowerShell:

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\keys"
& "C:\Program Files\Android\Android Studio\jbr\bin\keytool.exe" -genkeypair -v `
  -keystore "$env:USERPROFILE\keys\jainpanchang-upload.jks" -storetype JKS `
  -keyalg RSA -keysize 2048 -validity 10000 -alias upload
```

It asks for a keystore password and your name and organisation. With
`-storetype JKS` it then asks for a key password; pressing Enter reuses the
keystore password.

Then create `mobile/app/android/key.properties`. It is gitignored, along with
`*.jks` and `*.keystore`. Use forward slashes in the path, because a
`.properties` file treats `\` as an escape:

```properties
storeFile=C:/Users/<you>/keys/jainpanchang-upload.jks
storePassword=<keystore password>
keyAlias=upload
keyPassword=<key password>
```

`android/app/build.gradle.kts` signs release builds with this file. If the file
is missing, the build falls back to the debug key. Gradle logs a warning, which
`flutter build` shows only with `-v`, so the signer check in step 2 is what
tells you. Play rejects a debug-signed bundle, so one cannot be uploaded by
mistake. If the file
exists but a field is blank or missing, the build fails and names the field.

## 2. Each release

1. Bump `version:` in `pubspec.yaml`. The part after `+` is the Android
   `versionCode`. It must be higher than every bundle uploaded before, on any
   track, so `0.1.0+1` → `0.1.1+2`. Commit the bump.
2. Build it from `mobile/app`:

   ```powershell
   flutter build appbundle --release
   ```

   The bundle is `build/app/outputs/bundle/release/app-release.aab`.
3. Check it was signed with the upload key, not the debug key:

   ```powershell
   & "C:\Program Files\Android\Android Studio\jbr\bin\keytool.exe" -printcert -jarfile build\app\outputs\bundle\release\app-release.aab
   ```

   The owner should be the name you entered, not `CN=Android Debug`.

Build settings, for reference: `minSdk` 24 and `targetSdk` 36 come from
Flutter 3.47's defaults. Play has required target API 36 for new apps and
updates since 31 Aug 2026. The Flutter Gradle plugin turns on R8 minify and
resource shrinking for release builds.

## 3. Play Console checklist (first upload)

Account and app:

- [ ] Personal developer account ($25), with identity and contact details
      verified.
- [ ] **Create app**: name *Jain Panchang*, default language Hindi (hi-IN) or
      English, App, Free. Accept the declarations.

**Test and release → Internal testing:**

- [ ] **Testers**: create an email list (up to 100 Google accounts) and save it.
- [ ] **Create new release**: accept Play App Signing (Google-generated key),
      upload `app-release.aab`, and name the release (for example `0.1.0 (1)`).
- [ ] Review and roll out, then copy the **opt-in link** from the Testers tab
      and send it to the testers. Each tester opens it on the phone signed in
      with the listed account, then installs from Play.

**App content (Policy → App content)**. Play asks for these before the first
release; the app is free, offline and collects nothing:

- [ ] **Privacy policy**: host [`PRIVACY.md`](PRIVACY.md) at a public URL (for
      example Google Sites or a public gist; the repo is private) and paste the
      URL.
- [ ] **Ads**: no ads.
- [ ] **App access**: all functionality is available without special access.
- [ ] **Content rating**: fill in the IARC questionnaire with a contact email.
      Use the category *Reference, News or Educational* and answer **No** to
      every content question. It should come out as Everyone / 3+.
- [ ] **Target audience**: 13 and over (or 18 and over). Do not include
      under-13s, which brings in the Families policy. Not designed for
      children.
- [ ] **Data safety**: "Does your app collect or share any of the required user
      data types?" **No**. All data is processed on the device and nothing
      is sent off it. When opt-in crash reporting (Sentry) is wired in Phase 7,
      this answer changes to "collects crash logs and diagnostics, optional,
      not shared", and the privacy policy must say so first.
- [ ] **Advertising ID**: the app does not use it.
- [ ] Government app: no. Financial features: none. Health: none. News app: no.

**Main store listing** (short and full description, 512 × 512 icon, feature
graphic 1024 × 500, at least 2 phone screenshots). Internal testing does not
need it, but closed testing and production do. The 512 px icon is the
siddhashila mark on Navpad red; export it from
`android/app/src/main/res/drawable/ic_launcher_foreground.xml`.

## 4. Getting to production (personal accounts)

Re-checked on 30 Oct 2026 against Play Console Help, *App testing requirements
for new personal developer accounts*. A personal account created after
13 Nov 2023 must run a **closed test with at least 12 testers who stay opted in
for at least 14 consecutive days** before it can apply for production access.
A tester who opts out before 14 days does not count. Internal testing does not
count toward this rule.

Plan: the sangh closed beta (plan §1a, launch gate) doubles as this test.
Create the closed testing track, add at least 12 sangh testers (aim for 15 or
more as a margin), keep them opted in for 14 days or more, then use **Apply for
production** on the Dashboard. Google reviews the application, which usually
takes about a week. Re-check the numbers again at Phase 7.
