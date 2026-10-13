"""Composants visuels réutilisés sur plusieurs écrans (cartes, badges)."""

import customtkinter as ctk

from config import theme


def card(master, **kwargs):
    """Une carte blanche standard (fond + bordure + coins arrondis)."""
    defaults = dict(
        fg_color=theme.COLOR_CARD,
        border_color=theme.COLOR_BORDER,
        border_width=1,
        corner_radius=theme.CORNER_RADIUS_CARD,
    )
    defaults.update(kwargs)
    return ctk.CTkFrame(master, **defaults)


class MetricCard(ctk.CTkFrame):
    """Carte chiffre-clé : libellé, valeur, et variation optionnelle."""

    def __init__(self, master, label, value, delta=None, delta_positive=True, **kwargs):
        super().__init__(
            master, fg_color=theme.COLOR_CARD, border_color=theme.COLOR_BORDER,
            border_width=1, corner_radius=theme.CORNER_RADIUS_CARD, **kwargs,
        )
        ctk.CTkLabel(
            self, text=label, font=(theme.FONT_FAMILY, 12),
            text_color=theme.COLOR_TEXT_SECONDARY,
        ).pack(anchor="w", padx=16, pady=(14, 2))
        ctk.CTkLabel(
            self, text=value, font=(theme.FONT_FAMILY, 26, "bold"),
            text_color=theme.COLOR_TEXT_PRIMARY,
        ).pack(anchor="w", padx=16)
        if delta:
            color = theme.COLOR_SUCCESS if delta_positive else theme.COLOR_WARNING
            ctk.CTkLabel(
                self, text=delta, font=(theme.FONT_FAMILY, 11), text_color=color,
            ).pack(anchor="w", padx=16, pady=(2, 14))
        else:
            ctk.CTkFrame(self, height=10, fg_color="transparent").pack()


class StatusBadge(ctk.CTkLabel):
    """Petite étiquette colorée pour un statut (Actif, En attente, Approuvé...)."""

    PALETTE = {
        "success": (theme.COLOR_SUCCESS, theme.COLOR_SUCCESS_BG),
        "warning": (theme.COLOR_WARNING, theme.COLOR_WARNING_BG),
        "danger": (theme.COLOR_DANGER, theme.COLOR_DANGER_BG),
        "info": (theme.COLOR_INFO, theme.COLOR_INFO_BG),
    }

    def __init__(self, master, text, variant="info", **kwargs):
        fg, bg = self.PALETTE.get(variant, self.PALETTE["info"])
        super().__init__(
            master, text=text, text_color=fg, fg_color=bg,
            corner_radius=theme.CORNER_RADIUS_CONTROL, font=(theme.FONT_FAMILY, 11, "bold"),
            padx=10, pady=3, **kwargs,
        )


class HorizontalBar(ctk.CTkFrame):
    """Barre de progression horizontale étiquetée, utilisée pour 'Analyse par service'."""

    def __init__(self, master, label, percent, color=theme.COLOR_ACCENT, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x")
        ctk.CTkLabel(
            top, text=label, font=(theme.FONT_FAMILY, 12), text_color=theme.COLOR_TEXT_PRIMARY,
        ).pack(side="left")
        ctk.CTkLabel(
            top, text=f"{percent}%", font=(theme.FONT_FAMILY, 12, "bold"), text_color=color,
        ).pack(side="right")
        bar_bg = ctk.CTkFrame(self, height=8, fg_color=theme.COLOR_BORDER, corner_radius=4)
        bar_bg.pack(fill="x", pady=(4, 10))
        bar_bg.pack_propagate(False)
        fill = ctk.CTkFrame(bar_bg, fg_color=color, corner_radius=4)
        fill.place(relx=0, rely=0, relwidth=max(percent / 100, 0.03), relheight=1)


# ---------------------------------------------------------------------------
# Carte KPI colorée avec badge d'icône (icônes fournies par ui.icons)
# ---------------------------------------------------------------------------

class IconMetricCard(ctk.CTkFrame):
    """Carte chiffre-clé colorée avec badge d'icône, dans le style d'un
    tableau de bord professionnel (fond pastel + icône ronde + valeur)."""

    def __init__(self, master, icone_fn, label, value, delta=None, delta_positive=True,
                 couleur_fond="#dbeafe", couleur_badge="#2563eb", **kwargs):
        super().__init__(master, fg_color=couleur_fond, corner_radius=theme.CORNER_RADIUS_CARD,
                          border_width=0, **kwargs)

        self._icone = icone_fn("white", taille=22)  # référence gardée : évite le garbage-collect

        badge = ctk.CTkFrame(self, width=44, height=44, corner_radius=22, fg_color=couleur_badge)
        badge.pack(anchor="w", padx=16, pady=(16, 8))
        badge.pack_propagate(False)
        ctk.CTkLabel(badge, image=self._icone, text="").pack(expand=True)

        ctk.CTkLabel(
            self, text=label, font=(theme.FONT_FAMILY, 12), text_color=theme.COLOR_TEXT_SECONDARY,
        ).pack(anchor="w", padx=16)
        ctk.CTkLabel(
            self, text=value, font=(theme.FONT_FAMILY, 24, "bold"), text_color=theme.COLOR_TEXT_PRIMARY,
        ).pack(anchor="w", padx=16, pady=(0, 4))
        if delta:
            couleur_delta = theme.COLOR_SUCCESS if delta_positive else theme.COLOR_DANGER
            fleche = "↑" if delta_positive else "↓"
            ctk.CTkLabel(
                self, text=f"{fleche} {delta}", font=(theme.FONT_FAMILY, 11, "bold"),
                text_color=couleur_delta,
            ).pack(anchor="w", padx=16, pady=(0, 16))
        else:
            ctk.CTkFrame(self, height=12, fg_color="transparent").pack()