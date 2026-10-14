using System;
using UnityEngine;
using UnityEngine.EventSystems;

namespace Abyss.UI
{
    /// <summary>Invokes <see cref="Tapped"/> on a click/tap that was not a drag (safe on scroll viewports).</summary>
    public sealed class UITapArea : MonoBehaviour, IPointerClickHandler
    {
        public event Action Tapped;

        public void OnPointerClick(PointerEventData e)
        {
            if (e.dragging) return;
            Tapped?.Invoke();
        }
    }
}
