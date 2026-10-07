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
                    else EnterDungeonVisual();
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

        public void EnterTown()
        {
            SetPaused(false);
            Dungeon = null;
            var notices = GameFlow.EnterTown(State);
            EnterTownVisual();
            Save();
            ShowTownNotices(notices, 0);
        }

        /// <summary>Tips and elder lines carry different speakers, so each notice is shown under its own title.</summary>
        void ShowTownNotices(IReadOnlyList<StoryNotice> notices, int index)
        {
            if (index >= notices.Count) { if (index > 0) { Screen = GameScreen.Town; UI.ShowTown(); } return; }
            var notice = notices[index];
            ShowStory(DB.T(notice.TitleKey), new[] { DB.T(notice.TextKey) }, () => ShowTownNotices(notices, index + 1));
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
            Dungeon = new DungeonRun(DB, State, floorIndex, ArrivalMode.Town);
            EnterDungeonVisual();
            Save();
            var intro = Dungeon.ArrivalNotice;
            if (intro != null) ShowStory(DB.T(intro.TitleKey), new[] { DB.T(intro.TextKey) }, () => { Screen = GameScreen.Dungeon; UI.ShowDungeon(); Save(); });
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
            if (result.FloorChanged) { EnterDungeonVisual(); Save(); }
            else { dungeonWorld.RefreshProgress(); UI.RefreshDungeon(); }
            if (result.Effect == DungeonEffect.Trap) NotifyTip("first_trap");
            NotifyVisibleFoe();
            if (result.Effect == DungeonEffect.Treasure && result.Treasure != null) UI.ShowLoot(result.Treasure);
            else if (!string.IsNullOrEmpty(result.TextKey)) Notify(DB.T(result.TextKey, result.Args));
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
            Action route = () =>
            {
                if (resolution.Ending) ShowEnding();
                else if (resolution.ReturnToTown) EnterTown();
                else EnterDungeonVisual();
            };
            if (!string.IsNullOrEmpty(resolution.PostText)) ShowStory(DB.T("lore"), new[] { resolution.PostText }, route);
            else route();
        }

        public void ReturnToTown()
        {
            Dungeon?.ReturnToTown();
            EnterTown();
        }
        public void RecoverFromDefeat() { GameFlow.RecoverFromDefeat(DB, State); EnterTown(); }
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
                case "ember_caverns": return "bgm_desert";
                default: return "bgm_abyss";
            }
        }
    }
}
