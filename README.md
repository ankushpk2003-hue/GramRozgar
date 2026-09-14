# GramRozgar

Welcome to the **GramRozgar** repository! Below is the breakdown of our branch structure and team ownership.

---

## 🌿 Branch Overview & Assignments

| Branch | Contributor / Lead | Status / Instructions |
|---|---|---|
| `research` | Chinmay / Lead | Updated with the latest research documentation. |
| `frontend` | Aditya | Dedicated to frontend development. |
| `backend` | Akhil| Branch is set up. Switch to `backend` before pushing backend code. |
| `map` | Arpita | Ready for spatial implementation. If real data is unavailable, mock data will be used. |

---

# Git & GitHub Quick Guide

A single-line, copy-paste reference to get set up and push your work without conflicts.

---

### 1. First-Time Setup
Clone the repository, open the project folder, and switch directly to your assigned branch:

```bash
git clone <REPO_URL> && cd <REPO_FOLDER_NAME> && git checkout <branch-name>
```

---

### 2. Before Coding (Daily Sync)
Always run this before starting your work to pull the latest changes:

```bash
git pull origin <branch-name>
```

---

### 3. Save & Push (All-in-One Command)
When you are done coding, run this single line to stage, commit, and push your updates to GitHub:

```bash
git add . && git commit -m "Updated code" && git push origin <branch-name>
```

---

### 4. Useful Check
Check your current branch and see any modified files anytime:

```bash
git status
```

Do not commit to main: Keep all commits inside your designated branch.

Lost or confused? Run git status anytime to see your current branch and untracked changes.
