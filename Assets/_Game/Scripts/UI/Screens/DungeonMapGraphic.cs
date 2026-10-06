using Abyss.Logic.Dungeon;
using Abyss.Logic.Game;
using UnityEngine;
using UnityEngine.UI;

namespace Abyss.UI
{
    /// <summary>Draws only discovered tiles, retaining the original hidden-trap and spent-treasure rules.</summary>
    [RequireComponent(typeof(CanvasRenderer))]
    public sealed class DungeonMapGraphic : MaskableGraphic
    {
        DungeonGrid grid;
        GameState state;
        public void SetMap(DungeonGrid value, GameState current)
        { grid = value; state = current; raycastTarget = false; SetVerticesDirty(); }
        protected override void OnPopulateMesh(VertexHelper vh)
        {
            vh.Clear();
            if (grid == null || state == null) return;
            var bounds = rectTransform.rect;
            float unit = Mathf.Min(bounds.width / grid.Width, bounds.height / grid.Height);
            float left = bounds.center.x - grid.Width * unit * 0.5f;
            float top = bounds.center.y + grid.Height * unit * 0.5f;
            for (int y = 0; y < grid.Height; y++)
                for (int x = 0; x < grid.Width; x++)
                {
                    var p = new GridPos(x, y);
                    char marker = grid.MapMarker(p);
                    if (marker == ' ') continue;
                    var c = TileColor(marker);
                    Quad(vh, left + x * unit + 1, top - (y + 1) * unit + 1, unit - 2, c);
                    if (marker != '#' && marker != '.' && marker != 'S')
                        DrawSymbol(vh, marker, new Rect(left + x * unit, top - (y + 1) * unit, unit, unit));
                }
            // FOEs only appear on explored cells; a chasing FOE ('f') gets an orange alert frame.
            foreach (var foe in grid.Foes)
                if (foe.Alive && grid.Progress.Explored.Contains(foe.Position))
                    DrawSymbol(vh, foe.Chasing ? 'f' : 'F', new Rect(left + foe.Position.X * unit, top - (foe.Position.Y + 1) * unit, unit, unit));
            float px = left + (state.Position.X + 0.5f) * unit;
            float py = top - (state.Position.Y + 0.5f) * unit;
            var direction = state.Position.Step(state.Facing);
            var forward = new Vector2(direction.X - state.Position.X, state.Position.Y - direction.Y);
            var side = new Vector2(-forward.y, forward.x);
            int start = vh.currentVertCount;
            vh.AddVert(new Vector3(px + forward.x * unit * 0.43f, py + forward.y * unit * 0.43f), UITheme.DawnBright, Vector2.zero);
            vh.AddVert(new Vector3(px - forward.x * unit * 0.27f + side.x * unit * 0.3f, py - forward.y * unit * 0.27f + side.y * unit * 0.3f), UITheme.DawnBright, Vector2.zero);
            vh.AddVert(new Vector3(px - forward.x * unit * 0.27f - side.x * unit * 0.3f, py - forward.y * unit * 0.27f - side.y * unit * 0.3f), UITheme.DawnBright, Vector2.zero);
            vh.AddTriangle(start, start + 1, start + 2);
        }
        static Color TileColor(char marker)
        {
            switch (marker)
            {
                case '#': return UITheme.Ink;
                case 'W': return UITheme.Mp;
                case 'H': return UITheme.Positive;
                case 'B': case 'E': case 'X': return UITheme.Danger;
                case 'L': case 'K': case 'T': return UITheme.GoldDim;
                case '<': case '>': return UITheme.Dawn;
                case 'N': return new Color(0.55f, 0.43f, 0.85f);
                default: return new Color(0.2f, 0.29f, 0.43f);
            }
        }
        internal static void DrawSymbol(VertexHelper vh, char marker, Rect rect)
        {
            float x = rect.center.x, y = rect.center.y, u = Mathf.Min(rect.width, rect.height);
            Color color = marker == 'F' || marker == 'B' || marker == 'E' || marker == 'X' ? UITheme.Danger
                : marker == 'f' ? UITheme.Dawn : marker == 'H' ? UITheme.Positive : marker == 'W' ? UITheme.Mp : UITheme.GoldBright;
            float thin = Mathf.Max(1, u * 0.08f), arm = u * 0.28f;
            switch (marker)
            {
                case '>': case '<':
                    float sign = marker == '>' ? -1 : 1;
                    Triangle(vh, new Vector2(x, y + sign * arm), new Vector2(x - arm, y - sign * arm), new Vector2(x + arm, y - sign * arm), color);
                    break;
                case 'W': case 'K':
                    Triangle(vh, new Vector2(x, y + arm), new Vector2(x - arm, y), new Vector2(x + arm, y), color);
                    Triangle(vh, new Vector2(x, y - arm), new Vector2(x - arm, y), new Vector2(x + arm, y), color);
                    if (marker == 'K') Rectangle(vh, x, y - u * 0.4f, thin, arm, color);
                    break;
                case 'H':
                    Rectangle(vh, x - arm, y - thin * 0.5f, arm * 2, thin, color);
                    Rectangle(vh, x - thin * 0.5f, y - arm, thin, arm * 2, color);
                    break;
                case 'L':
                    Rectangle(vh, x - arm, y - arm, thin, arm * 2, color);
                    Rectangle(vh, x + arm - thin, y - arm, thin, arm * 2, color);
                    Rectangle(vh, x - arm, y + arm - thin, arm * 2, thin, color);
                    break;
                case 'T':
                    Rectangle(vh, x - arm, y - arm, arm * 2, thin, color);
                    Rectangle(vh, x - arm, y + arm - thin, arm * 2, thin, color);
                    Rectangle(vh, x - arm, y - arm, thin, arm * 2, color);
                    Rectangle(vh, x + arm - thin, y - arm, thin, arm * 2, color);
                    Rectangle(vh, x - thin * 0.5f, y - arm, thin, arm * 2, color);
                    break;
                case 'N':
                    Rectangle(vh, x - arm, y - arm, arm * 2, arm * 2, color);
                    Rectangle(vh, x - arm * 0.7f, y, arm * 1.4f, thin, UITheme.Ink);
                    Rectangle(vh, x - arm * 0.7f, y - arm * 0.55f, arm * 1.4f, thin, UITheme.Ink);
                    break;
                case 'X':
                    Triangle(vh, new Vector2(x - arm, y - arm), new Vector2(x - arm + thin, y - arm), new Vector2(x + arm, y + arm), color);
                    Triangle(vh, new Vector2(x + arm, y - arm), new Vector2(x + arm - thin, y - arm), new Vector2(x - arm, y + arm), color);
                    break;
                case 'B':
                    Rectangle(vh, x - arm, y - arm, arm * 2, thin * 2, color);
                    for (int i = -1; i <= 1; i++)
                        Triangle(vh, new Vector2(x + i * arm * 0.8f, y + arm), new Vector2(x + i * arm * 0.8f - thin, y - arm), new Vector2(x + i * arm * 0.8f + thin, y - arm), color);
                    break;
                case 'f':
                    float edge = u * 0.46f;
                    Rectangle(vh, x - edge, y - edge, edge * 2, thin, color);
                    Rectangle(vh, x - edge, y + edge - thin, edge * 2, thin, color);
                    Rectangle(vh, x - edge, y - edge, thin, edge * 2, color);
                    Rectangle(vh, x + edge - thin, y - edge, thin, edge * 2, color);
                    Triangle(vh, new Vector2(x, y + arm), new Vector2(x - arm, y - arm), new Vector2(x + arm, y - arm), color);
                    Rectangle(vh, x - thin * 0.5f, y - arm * 0.3f, thin, arm * 0.7f, UITheme.Ink);
                    Rectangle(vh, x - thin * 0.5f, y - arm * 0.8f, thin, thin, UITheme.Ink);
                    break;
                default:
                    Triangle(vh, new Vector2(x, y + arm), new Vector2(x - arm, y - arm), new Vector2(x + arm, y - arm), color);
                    if (marker == 'F') Rectangle(vh, x - thin * 0.5f, y - arm * 0.7f, thin, arm, UITheme.Ink);
                    break;
            }
        }
        static void Triangle(VertexHelper vh, Vector2 a, Vector2 b, Vector2 c, Color color)
        {
            int start = vh.currentVertCount;
            vh.AddVert(a, color, Vector2.zero); vh.AddVert(b, color, Vector2.zero); vh.AddVert(c, color, Vector2.zero);
            vh.AddTriangle(start, start + 1, start + 2);
        }
        static void Rectangle(VertexHelper vh, float x, float y, float width, float height, Color color)
        {
            int start = vh.currentVertCount;
            vh.AddVert(new Vector3(x,y), color, Vector2.zero); vh.AddVert(new Vector3(x,y + height), color, Vector2.zero);
            vh.AddVert(new Vector3(x + width,y + height), color, Vector2.zero); vh.AddVert(new Vector3(x + width,y), color, Vector2.zero);
            vh.AddTriangle(start,start + 1,start + 2); vh.AddTriangle(start,start + 2,start + 3);
        }
        static void Quad(VertexHelper vh, float x, float y, float size, Color color)
        {
            int start = vh.currentVertCount;
            vh.AddVert(new Vector3(x, y), color, Vector2.zero);
            vh.AddVert(new Vector3(x, y + size), color, Vector2.zero);
            vh.AddVert(new Vector3(x + size, y + size), color, Vector2.zero);
            vh.AddVert(new Vector3(x + size, y), color, Vector2.zero);
            vh.AddTriangle(start, start + 1, start + 2);
            vh.AddTriangle(start, start + 2, start + 3);
        }
    }
}
