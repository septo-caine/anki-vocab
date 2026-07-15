# Anki → known_words.txt, no laptop required

Every 6 hours (or on demand), GitHub's servers log into AnkiWeb with your
account, sync your collection, and publish every graduated word in your
deck to `known_words.txt` in this repo. Review on your phone → sync →
the list updates itself.

## One-time setup (~10 minutes, all doable from a phone browser)

1. **Create the repo.** On github.com, create a new **public** repository,
   e.g. `anki-vocab`. (Public means the word list gets a plain URL that
   Claude/ChatGPT can fetch. Only the word list is public — never your
   credentials. Want it private instead? See the note at the bottom.)

2. **Add the two files.** Use "Add file → Create new file" and paste the
   contents in, typing the full path as the filename:
   - `sync_and_export.py`
   - `.github/workflows/update_words.yml` (typing the `/` characters
     creates the folders automatically)

3. **Add your AnkiWeb credentials as secrets.** Repo → Settings →
   Secrets and variables → Actions → "New repository secret":
   - `ANKIWEB_USERNAME` — your AnkiWeb email
   - `ANKIWEB_PASSWORD` — your AnkiWeb password

   Secrets are encrypted and never appear in logs or the repo. Don't put
   these anywhere else (not in the files, not in chats with AI assistants).

4. **Set your deck and field.** Edit `.github/workflows/update_words.yml`
   (pencil icon) and change the two `EDIT` lines: `DECK` is your exact
   deck name from Anki's deck list; `FIELD` is the note field holding the
   word (in Anki: Browse → click a card → the labels above each box).
   Core 2k/6k users: the field is `Vocabulary-Kanji`.

5. **Run it.** Actions tab → "Update known words" → "Run workflow".
   The first run does a full download of your collection (a minute or
   two); later runs are incremental and take seconds.

Your list is now always at:

```
https://raw.githubusercontent.com/<your-username>/<repo-name>/main/known_words.txt
```

Open that URL once to confirm, then paste it into your Claude project
instructions.

## Daily flow

Review on your phone → sync in the Anki app → done. The list refreshes on
the 6-hour schedule; for an instant refresh, open the GitHub app (or site),
Actions tab → Run workflow. Then open your Claude/ChatGPT project and ask
for a story.

## introduced_words.txt

A second list holding words that AI-generated stories introduced but that
haven't graduated in Anki yet. The story assistant appends to it (via the
GitHub connector); each sync run automatically removes any word that has
since appeared in `known_words.txt`. Never write to `known_words.txt`
directly — it is overwritten from Anki on every run.

## Notes

- **Sync safety:** the job only ever *downloads* from AnkiWeb
  (`upload=False`); it can't overwrite your real collection.
- **Schedule pausing:** GitHub pauses cron schedules after ~60 days of
  repo inactivity. The bot's own commits generally keep it alive; if it
  ever pauses, the Actions tab shows a one-click "Enable" button.
- **Keeping the list private:** Claude can't fetch from private repos, so
  the alternative is publishing the file to your own website — the deploy
  step in the workflow just needs swapping for your host's upload method
  (FTP/SSH/etc.).
