// Unity frame capture for studioigor: this is how the agent sees the game without a human.
//
// Put into the project as Assets/Editor/StudioCapture.cs (the Editor folder is required:
// the script uses UnityEditor and must not end up in the build).
//
// VERIFICATION: the file was compiled against Unity 6000.6 assemblies (UnityEngine/UnityEditor
// reference DLLs via dotnet). A real -batchmode run on this machine has not been
// done: play mode and the SRP path (URP/HDRP) are not verified live. First run
// in a new project — check the log and metrics.json.
//
// The easiest path, if a live editor with com.unity.pipeline is open:
//   unity command screenshot --output .studioigor/captures/x/frame_000.png --width 1280 --height 720
// This file is for when there is no editor (CAPTURE in ENV.md, subagents, overnight runs).
//
// render mode (default) — a shot of the scene as it is on disk, without Play Mode:
// cameras render into a RenderTexture. Works via `unity run` (it adds
// -batchmode and -quit itself):
//   unity run . -- -executeMethod StudioCapture.Run \
//       -studioScene Assets/Scenes/Gyms/DriftGym.unity -studioOut .studioigor/captures/drift \
//       [-studioWidth 1280 -studioHeight 720] [-studioCamera "Main Camera"]
//
// play mode — the scene plays for N seconds, frames on a game-time schedule
// (Time.captureFramerate fixes the step). It needs a run WITHOUT -quit, so not via
// `unity run` but with the editor binary directly:
//   "$UNITY" -batchmode -projectPath . -logFile - -executeMethod StudioCapture.Run \
//       -studioScene Assets/Scenes/Gyms/DriftGym.unity -studioOut .studioigor/captures/drift \
//       -studioPlay -studioDuration 8 -studioEvery 1 [-studioStart 0.25] [-studioFps 60]
//   where UNITY="$(unity editors path <version>)/Contents/MacOS/Unity" or
//   /Applications/Unity/Hub/Editor/<version>/Unity.app/Contents/MacOS/Unity
//
// Other flags: -studioAllowErrors (do not fail on Error/Exception in the log),
// -studioTimeout 180 (seconds of real time for everything).
//
// Writes to -studioOut: frame_000.png …, metrics.json. Contact sheet — ImageMagick:
//   magick montage <out>/frame_*.png -tile 4x -geometry 480x270+2+2 <out>/sheet.png
// Exit: 0 — ok; 1 — failure (scene did not open, no camera/frames, errors in the log,
// did not enter Play Mode, timeout); 2 — invalid run (no -studioScene, play with -quit).
//
// Limitations: no -nographics (it produces no pixels). UI in Screen Space -
// Overlay mode is switched to Screen Space - Camera for the frame, otherwise the camera
// does not see it; the changes are not saved. There is no scheduled input here: for
// scripted input use the Input System InputTestFixture in a PlayMode test or
// a replay component in the game itself.

using System;
using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;

[InitializeOnLoad]
public static class StudioCapture
{
    const string K = "StudioCapture.";

    [Serializable]
    class Metrics
    {
        public bool ok;
        public string mode;
        public string scene;
        public string unity;
        public string pipeline;
        public int width;
        public int height;
        public float game_time;
        public double wall_time;
        public string[] frames;
        public int error_count;
        public string[] errors;
        public string[] fail_reasons;
    }

    static readonly List<string> Errors = new List<string>();

    // Entering Play Mode reloads the domain: statics are reset, and the
    // continuation lives in SessionState. This constructor re-attaches the handlers.
    static StudioCapture()
    {
        if (!SessionState.GetBool(K + "active", false)) return;
        Errors.AddRange(Load("errors"));
        Application.logMessageReceived += OnLog;
        EditorApplication.update += Tick;
    }

    // ------------------------------------------------------------------ entry

    public static void Run()
    {
        var args = Environment.GetCommandLineArgs();
        string scene = Arg(args, "-studioScene", "");
        string outDir = Arg(args, "-studioOut", ".studioigor/captures/unity");
        bool play = Has(args, "-studioPlay");

        if (string.IsNullOrEmpty(scene))
        {
            Debug.LogError("StudioCapture: -studioScene Assets/…/X.unity is required");
            EditorApplication.Exit(2);
            return;
        }
        if (play && Has(args, "-quit"))
        {
            Debug.LogError("StudioCapture: -studioPlay is incompatible with -quit (`unity run` adds it). " +
                           "Run the Unity binary directly without -quit.");
            EditorApplication.Exit(2);
            return;
        }

        outDir = Path.GetFullPath(outDir); // relative to the project root (the editor's cwd)
        Directory.CreateDirectory(outDir);
        foreach (var f in Directory.GetFiles(outDir, "frame_*.png")) File.Delete(f);

        SessionState.SetString(K + "scene", scene);
        SessionState.SetString(K + "out", outDir);
        SessionState.SetInt(K + "w", int.Parse(Arg(args, "-studioWidth", "1280")));
        SessionState.SetInt(K + "h", int.Parse(Arg(args, "-studioHeight", "720")));
        SessionState.SetString(K + "camera", Arg(args, "-studioCamera", ""));
        SessionState.SetBool(K + "allowErrors", Has(args, "-studioAllowErrors"));
        SessionState.SetFloat(K + "duration", Flt(args, "-studioDuration", 8f));
        SessionState.SetFloat(K + "every", Mathf.Max(0.02f, Flt(args, "-studioEvery", 1f)));
        SessionState.SetFloat(K + "next", Flt(args, "-studioStart", 0.25f));
        SessionState.SetInt(K + "fps", (int)Flt(args, "-studioFps", 60f));
        SessionState.SetFloat(K + "deadline",
            (float)(EditorApplication.timeSinceStartup + Flt(args, "-studioTimeout", 180f)));
        SessionState.SetFloat(K + "t0", (float)EditorApplication.timeSinceStartup);
        SessionState.SetString(K + "frames", "");
        SessionState.SetString(K + "errors", "");
        SessionState.SetInt(K + "waitPlay", 0);

        Application.logMessageReceived += OnLog;

        if (AssetDatabase.LoadAssetAtPath<SceneAsset>(scene) == null)
        {
            Finish(1, "render", "scene not found: " + scene);
            return;
        }
        try
        {
            EditorSceneManager.OpenScene(scene, OpenSceneMode.Single);
        }
        catch (Exception e)
        {
            Finish(1, "render", "scene did not open: " + e.Message);
            return;
        }

        if (!play)
        {
            var cam = FindCamera();
            if (cam == null) { Finish(1, "render", "no camera in the scene"); return; }
            string err = Shot(cam, 0);
            Finish(err == null ? 0 : 1, "render", err);
            return;
        }

        SessionState.SetBool(K + "active", true);
        EditorApplication.update += Tick;
        EditorApplication.EnterPlaymode();
        // Continues in Tick() after the domain reload.
    }

    // ------------------------------------------------------------------ play mode

    static void Tick()
    {
        if (!SessionState.GetBool(K + "active", false)) { EditorApplication.update -= Tick; return; }

        if (EditorApplication.timeSinceStartup > SessionState.GetFloat(K + "deadline", 0f))
        {
            Finish(1, "play", "real-time timeout");
            return;
        }
        if (!EditorApplication.isPlaying)
        {
            int w = SessionState.GetInt(K + "waitPlay", 0) + 1;
            SessionState.SetInt(K + "waitPlay", w);
            if (w > 3000) Finish(1, "play", "did not enter Play Mode (compile errors? Safe Mode?)");
            return;
        }

        int fps = SessionState.GetInt(K + "fps", 60);
        if (Time.captureFramerate != fps) Time.captureFramerate = fps;

        float t = Time.timeSinceLevelLoad;
        float next = SessionState.GetFloat(K + "next", 0.25f);
        float duration = SessionState.GetFloat(K + "duration", 8f);
        if (t >= next && next <= duration + 1e-4f)
        {
            var cam = FindCamera();
            if (cam == null) { Finish(1, "play", "no camera in the scene"); return; }
            string err = Shot(cam, Load("frames").Length);
            if (err != null) { Finish(1, "play", err); return; }
            SessionState.SetFloat(K + "next", next + SessionState.GetFloat(K + "every", 1f));
        }
        if (t >= duration) Finish(0, "play", null);
    }

    // ------------------------------------------------------------------ capture

    static Camera FindCamera()
    {
        string name = SessionState.GetString(K + "camera", "");
        if (!string.IsNullOrEmpty(name))
        {
            var go = GameObject.Find(name);
            return go != null ? go.GetComponent<Camera>() : null;
        }
        if (Camera.main != null) return Camera.main;
        Camera best = null;
        foreach (var c in Camera.allCameras) if (best == null || c.depth > best.depth) best = c;
        return best;
    }

    // Returns null on success, otherwise the error text.
    static string Shot(Camera cam, int index)
    {
        int w = SessionState.GetInt(K + "w", 1280), h = SessionState.GetInt(K + "h", 720);
        string path = Path.Combine(SessionState.GetString(K + "out", "."), $"frame_{index:000}.png");
        var rt = RenderTexture.GetTemporary(w, h, 24, RenderTextureFormat.ARGB32, RenderTextureReadWrite.Default);
        var prevTarget = cam.targetTexture;
        var prevActive = RenderTexture.active;
        var swapped = OverlayToCamera(cam);
        Texture2D tex = null;
        try
        {
            bool viaRequest = false;
            if (GraphicsSettings.currentRenderPipeline != null)
            {
                var req = new RenderPipeline.StandardRequest { destination = rt };
                if (RenderPipeline.SupportsRenderRequest(cam, req))
                {
                    RenderPipeline.SubmitRenderRequest(cam, req);
                    viaRequest = true;
                }
            }
            if (!viaRequest)
            {
                cam.targetTexture = rt;
                cam.Render();
            }
            RenderTexture.active = rt;
            tex = new Texture2D(w, h, TextureFormat.RGB24, false);
            tex.ReadPixels(new Rect(0, 0, w, h), 0, 0);
            tex.Apply();
            File.WriteAllBytes(path, tex.EncodeToPNG());
            Save("frames", Append(Load("frames"), Path.GetFileName(path)));
            return null;
        }
        catch (Exception e)
        {
            return "frame not captured: " + e.Message;
        }
        finally
        {
            cam.targetTexture = prevTarget;
            RenderTexture.active = prevActive;
            RenderTexture.ReleaseTemporary(rt);
            foreach (var c in swapped) { c.renderMode = RenderMode.ScreenSpaceOverlay; c.worldCamera = null; }
            if (tex != null) UnityEngine.Object.DestroyImmediate(tex);
        }
    }

    static List<Canvas> OverlayToCamera(Camera cam)
    {
        var swapped = new List<Canvas>();
        // Resources.FindObjectsOfTypeAll also sees assets — keep only scene objects.
        foreach (var c in Resources.FindObjectsOfTypeAll<Canvas>())
        {
            if (!c.gameObject.scene.IsValid() || !c.isActiveAndEnabled) continue;
            if (!c.isRootCanvas || c.renderMode != RenderMode.ScreenSpaceOverlay) continue;
            c.renderMode = RenderMode.ScreenSpaceCamera;
            c.worldCamera = cam;
            c.planeDistance = cam.nearClipPlane + 0.05f;
            swapped.Add(c);
        }
        if (swapped.Count > 0) Canvas.ForceUpdateCanvases();
        return swapped;
    }

    // ------------------------------------------------------------------ finish

    static void Finish(int code, string mode, string reason)
    {
        SessionState.SetBool(K + "active", false);
        EditorApplication.update -= Tick;
        Application.logMessageReceived -= OnLog;

        var fails = new List<string>();
        if (!string.IsNullOrEmpty(reason)) fails.Add(reason);
        var frames = Load("frames");
        if (frames.Length == 0 && fails.Count == 0) fails.Add("no frames captured");
        if (Errors.Count > 0 && !SessionState.GetBool(K + "allowErrors", false))
            fails.Add($"errors in the log: {Errors.Count} (first: {Errors[0]})");
        if (fails.Count > 0 && code == 0) code = 1;

        var rp = GraphicsSettings.currentRenderPipeline;
        var m = new Metrics
        {
            ok = code == 0,
            mode = mode,
            scene = SessionState.GetString(K + "scene", ""),
            unity = Application.unityVersion,
            pipeline = rp != null ? rp.GetType().Name : "Built-in",
            width = SessionState.GetInt(K + "w", 0),
            height = SessionState.GetInt(K + "h", 0),
            game_time = EditorApplication.isPlaying ? Time.timeSinceLevelLoad : 0f,
            wall_time = Math.Round(EditorApplication.timeSinceStartup - SessionState.GetFloat(K + "t0", 0f), 2),
            frames = frames,
            error_count = Errors.Count,
            errors = Errors.GetRange(0, Math.Min(20, Errors.Count)).ToArray(),
            fail_reasons = fails.ToArray(),
        };
        string outDir = SessionState.GetString(K + "out", ".");
        try { File.WriteAllText(Path.Combine(outDir, "metrics.json"), JsonUtility.ToJson(m, true) + "\n"); }
        catch (Exception e) { Debug.LogError("StudioCapture: metrics.json not written: " + e.Message); }

        if (code == 0) Debug.Log($"StudioCapture ok: {frames.Length} frames -> {outDir}");
        else foreach (var f in fails) Debug.LogError("CAPTURE FAILED: " + f);
        EditorApplication.Exit(code);
    }

    // ------------------------------------------------------------------ helpers

    static void OnLog(string message, string stack, LogType type)
    {
        if (type != LogType.Error && type != LogType.Exception && type != LogType.Assert) return;
        if (message.StartsWith("CAPTURE FAILED") || message.StartsWith("StudioCapture")) return;
        string line = message.Split('\n')[0];
        Errors.Add(line);
        Save("errors", Append(Load("errors"), line));
    }

    static string Arg(string[] a, string name, string dflt)
    {
        for (int i = 0; i < a.Length - 1; i++) if (a[i] == name) return a[i + 1];
        return dflt;
    }

    static bool Has(string[] a, string name) => Array.IndexOf(a, name) >= 0;

    static float Flt(string[] a, string name, float dflt) =>
        float.Parse(Arg(a, name, dflt.ToString(System.Globalization.CultureInfo.InvariantCulture)),
                    System.Globalization.CultureInfo.InvariantCulture);

    // Lists in SessionState are strings joined with \n.
    static string[] Load(string key)
    {
        string s = SessionState.GetString(K + key, "");
        return s.Length == 0 ? new string[0] : s.Split('\n');
    }

    static void Save(string key, string[] items) => SessionState.SetString(K + key, string.Join("\n", items));

    static string[] Append(string[] items, string item)
    {
        var l = new List<string>(items) { item.Replace('\n', ' ') };
        return l.ToArray();
    }
}
