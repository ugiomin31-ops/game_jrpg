// Console test harness for engine-free logic. Tests are static methods marked [LogicTest] in any file
// under Tools/LogicTests. Run with: python Tools/logic_test.py [name-filter]
using System;
using System.IO;
using System.Linq;
using System.Reflection;
using Abyss.Logic;

namespace Abyss.LogicTests
{
    [AttributeUsage(AttributeTargets.Method)]
    public sealed class LogicTestAttribute : Attribute { }

    public static class Assert
    {
        public static void True(bool cond, string msg) { if (!cond) throw new Exception("Assert failed: " + msg); }
        public static void Equal<T>(T expected, T actual, string msg)
        {
            if (!Equals(expected, actual)) throw new Exception($"Assert failed: {msg} (expected {expected}, got {actual})");
        }
        public static void Near(double expected, double actual, double eps, string msg)
        {
            if (Math.Abs(expected - actual) > eps) throw new Exception($"Assert failed: {msg} (expected {expected}±{eps}, got {actual})");
        }
    }

    public static class TestMain
    {
        public static GameDB DB;

        // ExpeditionReadinessTests are discovered with the other engine-free logic tests.
        // ActionPreviewTests are discovered with the other engine-free logic tests.
        // BattleDecisionMechanicsTests are discovered with the other engine-free logic tests.
        // EnemyIntentTests are discovered with the other engine-free logic tests.
        // FastBattleResultsTests are discovered with the other engine-free logic tests.
        // SpringAttritionTests are discovered with the other engine-free logic tests.
        // ResourceAttritionTests are discovered with the other engine-free logic tests.
        // StarterProgressionTests cover actual unboosted outings with real once-only settlement.

        public static int Main(string[] args)
        {
            string dir = Environment.GetEnvironmentVariable("ABYSS_DATA_DIR");
            DB = GameDB.Load(t => File.ReadAllText(Path.Combine(dir, t + ".json")));
            string filter = args.Length > 0 ? args[0] : "";
            var tests = AppDomain.CurrentDomain.GetAssemblies().SelectMany(a => a.GetTypes())
                .SelectMany(t => t.GetMethods(BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic))
                .Where(m => m.GetCustomAttribute<LogicTestAttribute>() != null)
                .Where(m => (m.DeclaringType.Name + "." + m.Name).IndexOf(filter, StringComparison.OrdinalIgnoreCase) >= 0)
                .OrderBy(m => m.DeclaringType.Name).ThenBy(m => m.Name).ToList();
            int fail = 0;
            foreach (var m in tests)
            {
                string name = m.DeclaringType.Name + "." + m.Name;
                try { m.Invoke(null, null); Console.WriteLine("PASS " + name); }
                catch (TargetInvocationException e) { fail++; Console.WriteLine("FAIL " + name + ": " + e.InnerException.Message + "\n" + e.InnerException.StackTrace); }
            }
            Console.WriteLine($"{tests.Count - fail}/{tests.Count} passed");
            return fail == 0 ? 0 : 1;
        }
    }

}
