using System;
using System.Collections.Generic;
using System.IO;
using Abyss.Logic;
using Abyss.Logic.Game;
using Abyss.Logic.Dungeon;
using Abyss.Runtime.World;
using Abyss.Runtime.Persistence;
using Abyss.Runtime.Battle;
using Abyss.Presentation.Audio;
using Abyss.UI;
using UnityEngine;

namespace Abyss.Runtime
{
    public enum GameScreen { Title, Story, Town, Dungeon, Battle, Ending }

    public sealed class GameApp : MonoBehaviour
    {
        public static GameApp Instance { get; private set; }
        public GameDB DB { get; private set; }
        public GameState State { get; private set; }
        public GameScreen Screen { get; private set; }
        public Camera MainCamera { get; private set; }
        public Transform WorldRoot { get; private set; }
        public Atmosphere Atmosphere { get; private set; }
        public GameUI UI { get; private set; }
        public DungeonRun Dungeon { get; private set; }
        public BattleView Battle { get; private set; }
        public GamePreferences Preferences { get; private set; }
        public SaveRepository Saves { get; private set; }
        public bool Paused { get; private set; }
        string saveDirectory;
        TownWorld townWorld;
        DungeonWorld dungeonWorld;

        void Awake()
        {
            if (Instance != null && Instance != this) { Destroy(gameObject); return; }
            Instance = this;
            DB = GameDB.Load(table =>
            {
                var asset = Resources.Load<TextAsset>("Data/" + table);
                if (asset == null) throw new InvalidOperationException("Missing game data: " + table);
                return asset.text;
            });
            saveDirectory = Path.Combine(Application.persistentDataPath, "campaign");
            Saves = new SaveRepository(saveDirectory, DB);
            Preferences = GamePreferences.Read(saveDirectory);
            var cameraObject = new GameObject("Main Camera", typeof(Camera), typeof(AudioListener));
            cameraObject.transform.SetParent(transform, false);
            cameraObject.tag = "MainCamera";
            MainCamera = cameraObject.GetComponent<Camera>();
            MainCamera.nearClipPlane = 0.08f;
            MainCamera.farClipPlane = 180f;
            MainCamera.fieldOfView = 55f;
            Atmosphere = Atmosphere.Create(transform);
            UI = new GameObject("Game UI").AddComponent<GameUI>();
            UI.transform.SetParent(transform, false);
            UI.Initialize(this);
            Preferences.Apply();
            ShowTitle();
        }

        void Update()
        {
            if (State != null && !Paused && Screen != GameScreen.Title) State.PlayTimeSeconds += Time.unscaledDeltaTime;
        }

        public void ApplyPreferences()
        {
            Preferences.Apply();
            SavePreferences();
        }

        /// <summary>Persists preferences that need no re-apply (e.g. battle speed changed mid-battle).</summary>
        public void SavePreferences()
        {
            try { Preferences.Save(saveDirectory); }
            catch (Exception e) when (e is IOException || e is UnauthorizedAccessException) { Notify("설정 저장 실패: " + e.Message); }
        }

        void ResetWorld()
        {
            if (WorldRoot != null) { WorldRoot.gameObject.SetActive(false); Destroy(WorldRoot.gameObject); }
            WorldRoot = new GameObject("World").transform;
            WorldRoot.SetParent(transform, false);
            townWorld = null;
            dungeonWorld = null;
            Battle = null;
            UI.Clear();
        }

        public void ShowTitle()
        {
            SetPaused(false);
            Screen = GameScreen.Title;
            Dungeon = null;
            ResetWorld();
            townWorld = WorldRoot.gameObject.AddComponent<TownWorld>();
            townWorld.Initialize(this, true);
            AudioManager.Instance.PlayBgm("bgm_title");
            UI.ShowTitle();
        }

        public void NewGame(Difficulty difficulty)
        {
            State = GameState.NewGame(DB, difficulty);
            Dungeon = null;
            ShowStory(DB.T("prologue_title"), Localize(GameFlow.PrologueKeys), () =>
            {
                GameFlow.CompletePrologue(State);
                EnterTown();
            });
        }

        public void Continue(int slot = -1)
        {
            try { State = Saves.Read(slot); }
            catch (Exception e) when (e is IOException || e is UnauthorizedAccessException || e is SaveFormatException)
            { Notify("저장 파일을 불러오지 못했습니다: " + e.Message); return; }
            SetPaused(false);
            Dungeon = null;
            switch (GameFlow.ResumeRouteOf(State))
            {
                case ResumeRoute.Prologue:
                    ShowStory(DB.T("prologue_title"), Localize(GameFlow.PrologueKeys), () => { GameFlow.CompletePrologue(State); EnterTown(); });
                    break;
                case ResumeRoute.GameOver:
                    EnterTownVisual(); UI.ShowDefeat(); break;
                case ResumeRoute.Ending:
                    ShowEnding(); break;
                case ResumeRoute.Dungeon:
                    Dungeon = new DungeonRun(DB, State, State.FloorIndex, ArrivalMode.Resume);
                    if (Dungeon.PendingBattle != null) BeginBattle(Dungeon.PendingBattle.Setup);
                    // The floor is rebuilt under the area card instead of hard-cutting from the title town.
                    else UI.Transition(() => UI.FloorCard(State.FloorIndex), EnterDungeonVisual);
                    break;
                default: EnterTown(); break;
            }
        }

        public void Save(int slot = -1)
        {
            if (State == null) return;
            try { Saves.Write(slot, State); if (slot >= 0) Notify("저장했습니다."); }
            catch (Exception e) when (e is IOException || e is UnauthorizedAccessException) { Notify("저장 실패: " + e.Message); }
        }

        /// <summary>
        /// Arrives in town behind the town area card: the town state update, world rebuild and save run while the card
        /// covers the screen. <paramref name="revealed"/> runs once the card has swept away (e.g. a toast to read).
        /// </summary>
        public void EnterTown(Action revealed = null)
        {
            SetPaused(false);
            UI.Transition(UI.TownCard, () =>
            {
                Dungeon = null;
                var notices = GameFlow.EnterTown(DB, State);
                EnterTownVisual();
                Save();
                ShowTownNotices(notices, 0);
            }, revealed);
        }

        /// <summary>Tips and elder lines carry different speakers, so each notice is shown under its own title.</summary>
        void ShowTownNotices(IReadOnlyList<StoryNotice> notices, int index)
        {
            if (index >= notices.Count) { if (index > 0) { Screen = GameScreen.Town; UI.ShowTown(); } return; }
            var notice = notices[index];
            ShowStory(DB.T(notice.TitleKey), new[] { notice.Text ?? DB.T(notice.TextKey) }, () => ShowTownNotices(notices, index + 1));
        }

        void EnterTownVisual()
        {
            Screen = GameScreen.Town;
            ResetWorld();
            townWorld = WorldRoot.gameObject.AddComponent<TownWorld>();
            townWorld.Initialize(this, false);
            AudioManager.Instance.PlayBgm("bgm_town");
            UI.ShowTown();
        }

        public void RefreshEquipmentVisuals() => townWorld?.RefreshEquipment();
        /// <summary>Swaps town party models to their current job outfits (after a class change).</summary>
        public void RefreshJobVisuals() => townWorld?.RefreshJobModels();
        /// <summary>Respawns the guild party and lounge after a roster change (party formation, scouting).</summary>
        public void RefreshRosterVisuals() => townWorld?.RefreshRoster();

        /// <summary>A facility screen opened: the town camera eases to a two-shot with that person when they are close.</summary>
        public void BeginTownTalk(string id) => townWorld?.BeginTalk(id);

        public void OpenTownService(string id)
        {
            if (Screen != GameScreen.Town || Paused) return;
            UI.ShowTownService(id);
        }

        public void Depart(int floorIndex)
        {
            var result = TownServices.Depart(DB, State, floorIndex);
            if (!result.Success) { Notify(result.Message(DB)); return; }
            SetPaused(false);
            // Town -> gate (start or warp floor): the dungeon is built while the area card covers the screen.
            UI.Transition(() => UI.FloorCard(State.FloorIndex), () =>
            {
                Dungeon = new DungeonRun(DB, State, floorIndex, ArrivalMode.Town);
                EnterDungeonVisual();
                Save();
                var intro = Dungeon.ArrivalNotice;
                if (intro != null) ShowStory(DB.T(intro.TitleKey), new[] { DB.T(intro.TextKey) }, () => { Screen = GameScreen.Dungeon; UI.ShowDungeon(); Save(); });
            });
        }

        void EnterDungeonVisual()
        {
            Screen = GameScreen.Dungeon;
            ResetWorld();
            dungeonWorld = WorldRoot.gameObject.AddComponent<DungeonWorld>();
            dungeonWorld.Initialize(this, Dungeon);
            AudioManager.Instance.PlayBgm(BiomeMusic(DB.Floors[State.FloorIndex].Tileset));
            UI.ShowDungeon();
            NotifyVisibleFoe();
        }

        public void MoveDungeon(RelativeMove direction) => dungeonWorld?.Move(direction);
        public void TurnDungeon(int quarterTurns) => dungeonWorld?.Turn(quarterTurns);
        public void InteractDungeon() => dungeonWorld?.Interact();
        public void WaitDungeon() => dungeonWorld?.WaitTurn();

        internal void HandleDungeonStep(DungeonStepResult result)
        {
            if (result.ReturnToTown) { EnterTown(); return; }
            if (result.FloorChanged)
            {
                // Stairs: the logic has already moved the party; the new floor is built under the area card and the
                // rest of the step (tips, notices, biome story) follows while it is still covered.
                UI.Transition(() => UI.FloorCard(State.FloorIndex), () => { EnterDungeonVisual(); Save(); FinishDungeonStep(result); });
                return;
            }
            dungeonWorld.RefreshProgress(); UI.RefreshDungeon();
            FinishDungeonStep(result);
        }

        void FinishDungeonStep(DungeonStepResult result)
        {
            if (result.Effect == DungeonEffect.Trap) NotifyTip("first_trap");
            NotifyVisibleFoe();
            if (result.Effect == DungeonEffect.Treasure && result.Treasure != null) UI.ShowLoot(result.Treasure);
            else if (!string.IsNullOrEmpty(result.TextKey)) Notify(DB.T(result.TextKey, result.Args));
            if (result.Battle == null && result.Effect == DungeonEffect.Rescue && result.Event != null)
            {
                // Spent flag and reward are already in the state: save before the story so a quit cannot replay or lose it.
                Save();
                var rescue = result.Event; var reward = result.Treasure;
                ShowStory(string.IsNullOrEmpty(rescue.Title) ? DB.T("lore") : rescue.Title, new[] { rescue.Text ?? "" }, () =>
                {
                    Screen = GameScreen.Dungeon; UI.ShowDungeon();
                    UI.ShowEventReward(DB.T("event_rescue_reward_title"), reward);
                });
                return;
            }
            if (result.Battle == null && result.Effect == DungeonEffect.Choice && result.Choice != null)
            {
                UI.ShowDungeonChoice(result.Choice, ResolveDungeonChoice, DismissDungeonChoice);
                return;
            }
            if (result.Battle != null)
            {
                Save();
                if (!string.IsNullOrEmpty(result.Battle.PreText))
                    ShowStory(DB.T("lore"), new[] { result.Battle.PreText }, () => BeginBattle(result.Battle.Setup));
                else BeginBattle(result.Battle.Setup);
            }
            else if (!string.IsNullOrEmpty(result.StoryText))
                ShowStory(DB.T("lore"), new[] { result.StoryText }, () => { Screen = GameScreen.Dungeon; UI.ShowDungeon(); });
            else if (result.BiomeNotice != null)
                ShowStory(DB.T(result.BiomeNotice.TitleKey), new[] { DB.T(result.BiomeNotice.TextKey) }, () => { Screen = GameScreen.Dungeon; UI.ShowDungeon(); Save(); });
        }

        /// <summary>Choice modal answer: leave spends the event; accept saves the pending event battle, then starts it.</summary>
        public void ResolveDungeonChoice(DungeonChoice choice, int option)
        {
            if (Dungeon == null || Screen != GameScreen.Dungeon) return;
            var outcome = Dungeon.ResolveChoice(choice, option);
            if (outcome.Rejected) { UI.RefreshDungeon(); return; }
            Save();
            if (outcome.Accepted && outcome.Battle != null) { BeginBattle(outcome.Battle.Setup); return; }
            dungeonWorld?.RefreshProgress();
            UI.RefreshDungeon();
            Notify(DB.T("event_choice_left"));
        }
        /// <summary>Choice modal closed without deciding: the nest stays and re-opens on Interact.</summary>
        public void DismissDungeonChoice(DungeonChoice choice)
        {
            if (Dungeon != null && Dungeon.DismissChoice(choice)) Notify(DB.T("event_choice_reopen"));
        }

        /// <summary>
        /// Review builds only (<see cref="ReviewBoot"/>, URL <c>?review=battle</c>): adopts a prepared campaign state standing on
        /// <paramref name="floorIndex"/> without the title, prologue or town, so battles can be started directly.
        /// </summary>
        public void BeginReview(GameState state, int floorIndex)
        {
            State = state ?? throw new ArgumentNullException(nameof(state));
            SetPaused(false);
            Dungeon = new DungeonRun(DB, State, floorIndex, ArrivalMode.Resume);
            EnterDungeonVisual();
        }

        public void BeginBattle(BattleSetup setup)
        {
            SetPaused(false);
            Screen = GameScreen.Battle;
            ResetWorld();
            Battle = WorldRoot.gameObject.AddComponent<BattleView>();
            Battle.Initialize(this, setup, FinishBattle);
            NotifyTip("first_battle");
        }

        public void FinishBattle(BattleOutcome outcome)
        {
            if (Dungeon == null) throw new InvalidOperationException("Battle has no campaign encounter.");
            var resolution = Dungeon.ResolveBattle(outcome);
            if (resolution.Defeat) { UI.Clear(); UI.ShowDefeat(); return; }
            // Choice-event contents were committed (and saved by the battle view) inside ResolveBattle; only show them here.
            var extra = resolution.ExtraReward;
            if (extra != null) Save();
            Action route = () =>
            {
                if (resolution.Ending) ShowEnding();
                else if (resolution.ReturnToTown) EnterTown();
                else
                {
                    EnterDungeonVisual();
                    if (extra != null) UI.ShowEventReward(DB.T("event_choice_reward_title"), extra);
                }
            };
            if (!string.IsNullOrEmpty(resolution.PostText)) ShowStory(DB.T("lore"), new[] { resolution.PostText }, route);
            else route();
        }

        public void ReturnToTown()
        {
            Dungeon?.ReturnToTown();
            EnterTown();
        }
        public void RecoverFromDefeat()
        {
            int lost = GameFlow.RecoverFromDefeat(DB, State);
            // The return screen names the gold the defeat took (once the town card has gone); nothing extra when it took none.
            EnterTown(() => { if (lost > 0) Notify(DB.T("defeat_gold_lost", lost.ToString("N0", System.Globalization.CultureInfo.InvariantCulture))); });
        }
        public void SetPaused(bool paused)
        {
            Paused = paused;
            Time.timeScale = paused ? 0f : 1f;
            AudioManager.Instance.SetPaused(paused);
        }
        public void Notify(string message) => UI.Notify(message);
        internal void NotifyTip(string key)
        {
            if (State == null || State.Flags.Contains(GameFlow.TipFlag(key))) return;
            UI.Notify(DB.T(GameFlow.TipFlag(key)));
            GameFlow.TryTip(State, key);
        }
        void NotifyVisibleFoe()
        {
            if (Dungeon == null) return;
            foreach (var foe in Dungeon.Grid.Foes)
                if (foe.Alive && Dungeon.Grid.Progress.Explored.Contains(foe.Position))
                {
                    NotifyTip("first_foe");
                    break;
                }
        }
        public void Quit()
        {
            if (State != null && Screen != GameScreen.Title && Screen != GameScreen.Battle) Save();
            ApplyPreferences();
#if UNITY_EDITOR
            UnityEditor.EditorApplication.isPlaying = false;
#else
            Application.Quit();
#endif
        }
        void OnApplicationQuit()
        {
            if (State != null && Screen != GameScreen.Title && Screen != GameScreen.Battle) Save();
        }
        // Phones rarely quit cleanly: the OS kills backgrounded apps, so autosave whenever the app is sent away.
        void OnApplicationPause(bool paused)
        {
            if (paused && Application.isMobilePlatform) OnApplicationQuit();
        }
        void OnDestroy()
        {
            if (Instance == this) { Instance = null; Time.timeScale = 1f; }
        }
        void ShowStory(string title, IReadOnlyList<string> lines, Action completed)
        {
            Screen = GameScreen.Story;
            UI.ShowStory(title, lines, completed);
        }
        void ShowEnding()
        {
            Screen = GameScreen.Ending;
            AudioManager.Instance.PlayBgm("bgm_ending");
            UI.ShowEnding(() => { GameFlow.MarkEndingSeen(State); EnterTown(); });
        }
        List<string> Localize(IReadOnlyList<string> keys)
        {
            var lines = new List<string>(keys.Count);
            foreach (string key in keys) lines.Add(DB.T(key));
            return lines;
        }
        static string BiomeMusic(string tileset)
        {
            switch (tileset)
            {
                case "verdant_ruins": return "bgm_forest";
                case "frost_grotto": return "bgm_frost";
                case "ember_caverns":
                case "cave": return "bgm_desert";
                case "guild_street": return "bgm_town";
                default: return "bgm_abyss";
            }
        }
    }
}
