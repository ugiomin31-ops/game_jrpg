using UnityEngine;
using UnityEngine.UI;

namespace Abyss.UI
{
    /// <summary>Legend swatches reuse exactly the same shapes as the explored map.</summary>
    [RequireComponent(typeof(CanvasRenderer))]
    public sealed class DungeonMapSymbol : MaskableGraphic
    {
        public char Marker;
        protected override void OnPopulateMesh(VertexHelper vh)
        {
            vh.Clear(); raycastTarget = false;
            DungeonMapGraphic.DrawSymbol(vh, Marker, rectTransform.rect);
        }
    }
}
