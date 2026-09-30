import marimo

__generated_with = "0.24.0"
app = marimo.App(width="medium", auto_download=["html"])


@app.cell(hide_code=True)
def _():
    import math

    import marimo as mo
    import matplotlib.pyplot as plt
    import numpy as np

    return math, mo, np, plt


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Verificación de machón de hormigón sobre cañería
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 1. Parámetros de entrada
    """)
    return


@app.cell
def _(mo):
    L_input = mo.ui.number(value=3.0, start=0.5, stop=20.0, step=0.001, label="Largo L (m)")
    H_input = mo.ui.number(value=1.5, start=0.3, stop=10.0, step=0.001, label="Alto H (m)")
    B_input = mo.ui.number(value=0.8, start=0.2, stop=5.0, step=0.001, label="Ancho B (m)")
    mo.hstack([L_input, H_input, B_input])
    return B_input, H_input, L_input


@app.cell
def _(mo):
    ancho_abertura_input = mo.ui.number(
        value=0.35, start=0.1, stop=2.0, step=0.001, label="Ancho de abertura (m)"
    )
    sep_input = mo.ui.number(
        value=0.5, start=0.0, stop=10.0, step=0.001, label="Separación entre cañerías, centro a centro (m)"
    )
    r_pipe_input = mo.ui.number(
        value=0.17, start=0.01, stop=2.0, step=0.001,
        label="Radio externo cañería / altura de aplicación de carga (m)",
    )
    n_pipes_input = mo.ui.radio(
            options=["1", "2"], value="2", label="Número de cañerías", inline=True
    )
    mo.vstack([mo.hstack([ancho_abertura_input, sep_input]), mo.hstack([r_pipe_input, n_pipes_input])])
    return ancho_abertura_input, n_pipes_input, r_pipe_input, sep_input


@app.cell
def _(mo):
    Q_tub_input = mo.ui.number(
        value=5.0, start=0.0, stop=1000.0, step=0.1,
        label="Carga transversal por cañería (kN)",
    )
    Cs_input = mo.ui.number(value=0.43, start=0.0, stop=2.0, step=0.01, label="Coeficiente sísmico Cs")
    mo.hstack([Q_tub_input, Cs_input])
    return Cs_input, Q_tub_input


@app.cell
def _(mo):
    gamma_c_input = mo.ui.number(
        value=2500.0, start=1800.0, stop=3000.0, step=10.0, label="Densidad hormigón γc (kg/m³)"
    )
    phi_input = mo.ui.number(value=32.0, start=15.0, stop=45.0, step=0.5, label="Ángulo de fricción suelo φ (°)")
    sigma_adm_input = mo.ui.number(
        value=20.0, start=1.0, stop=200.0, step=0.01, label="Capacidad de soporte admisible (t/m²)"
    )
    FSD_min_input = mo.ui.number(value=1.3, start=1.0, stop=3.0, step=0.05, label="FS mínimo exigido (desl.)")
    FSV_min_input = mo.ui.number(value=1.5, start=1.0, stop=3.0, step=0.05, label="FS mínimo exigido (volc.)")
    mo.vstack([mo.hstack([gamma_c_input, phi_input, sigma_adm_input]), mo.hstack([FSV_min_input, FSD_min_input])])
    return (
        FSD_min_input,
        FSV_min_input,
        gamma_c_input,
        phi_input,
        sigma_adm_input,
    )


@app.cell
def _(math, mo, phi_input):
    mu = math.tan(2/3*math.radians(phi_input.value))
    mo.md(f"Coeficiente de fricción hormigón-suelo estimado como `tan(2/3 φ)` → **μ = {mu:.3f}**")
    return (mu,)


@app.cell
def _(mo):

    pp_toggle_input = mo.ui.switch(
        value=False,
        label="Incluir presion pasiva del terreno",
    )
    D_emb_input = mo.ui.number(
        value=0.5, start=0.0, stop=5.0, step=0.05,
        label="Profundidad bajo terreno D_emb (m)",
    )
    gamma_suelo_input = mo.ui.number(
        value=18.0, start=12.0, stop=22.0, step=0.5,
        label="Peso unitario del suelo gamma_suelo (kN/m3)",
    )
    factor_mov_input = mo.ui.number(
        value=0.5, start=0.1, stop=1.0, step=0.05,
        label="Factor de movilizacion de Pp (1.0 = Rankine completo)",
    )
    mo.vstack([
        mo.hstack([D_emb_input, pp_toggle_input]),
        mo.hstack([gamma_suelo_input, factor_mov_input]),
    ])
    return D_emb_input, factor_mov_input, gamma_suelo_input, pp_toggle_input


@app.cell
def _(mo):
    mo.md("""
    ## 2. Geometría
    """)
    return


@app.cell
def _(
    B_input,
    D_emb_input,
    H_input,
    L_input,
    ancho_abertura_input,
    math,
    n_pipes_input,
    sep_input,
):
    L = L_input.value
    H = H_input.value
    B = B_input.value
    D_emb = min(D_emb_input.value, H)
    sep = sep_input.value
    n_pipes = int(n_pipes_input.value)

    r = ancho_abertura_input.value / 2.0

    # Geometria base de abertura
    A_rect = 2.0 * r * r
    A_semi = math.pi * r ** 2 / 2.0
    A_ab_base = A_semi + A_rect

    # Altura total de la abertura considerando la extension de 2*r sobre el nivel de terreno
    h_ext_sup = 2.0 * r
    h_ab_total = min(H, D_emb + h_ext_sup)

    z_rect = r / 2.0
    z_semi = r + (4.0 * r) / (3.0 * math.pi)
    z_ab = (A_rect * z_rect + A_semi * z_semi) / A_ab_base

    if n_pipes == 1:
        centros = [L / 2.0]
    else:
        centros = [L / 2.0 - sep / 2.0, L / 2.0 + sep / 2.0]

    warnings = []
    if h_ab_total > H:
        warnings.append(
            f"Warning: total opening height ({h_ab_total:.3f} m) exceeds H ({H:.3f} m)."
        )
    for xc in centros:
        if xc - r < 0 or xc + r > L:
            warnings.append(
                "Warning: opening exceeds machon boundaries in L direction."
            )
            break
    if n_pipes == 2 and (centros[0] + r > centros[1] - r):
        warnings.append("Warning: two openings overlap (check spacing).")

    # 1. GEOMETRIA TOTAL MACHON (para Resistencia al Deslizamiento y Volcamiento)
    A_gross = L * H
    A_ab_total = n_pipes * A_ab_base
    A_net = A_gross - A_ab_total
    z_gross = H / 2.0
    z_cg_net = (A_gross * z_gross - A_ab_total * z_ab) / A_net if A_net > 0 else 0.0
    V_net = A_net * B

    # 2. GEOMETRIA SOBRE TERRENO (para Determinacion de Cargas Sismicas)
    H_sup = max(0.0, H - D_emb)
    A_gross_sup = L * H_sup

    # Area de abertura que queda sobre el nivel de terreno (extension de 2*r sobre cota D_emb)
    h_sup_ab = min(H_sup, h_ext_sup)
    A_ab_sup = (2.0 * r) * h_sup_ab

    A_net_sup = max(0.0, A_gross_sup - n_pipes * A_ab_sup)
    V_net_sup = A_net_sup * B

    # Centroide de la masa aerea desde la base del machon (punto de aplicacion del sismo)
    z_cg_sup = D_emb + (H_sup / 2.0) if H_sup > 0 else z_cg_net
    return (
        A_ab_base,
        A_net,
        B,
        D_emb,
        H,
        L,
        V_net,
        V_net_sup,
        centros,
        h_ab_total,
        h_ext_sup,
        n_pipes,
        r,
        warnings,
        z_cg_net,
        z_cg_sup,
    )


@app.cell
def _(B, L, centros, r):
    # Sección en planta L×B con "huecos" (sin apoyo) en cada posición de cañería
    x_bar = L / 2.0  # centroide en planta (simétrico)

    A_base_net = B * (L - len(centros) * 2.0 * r)

    I_gross = B * L ** 3 / 12.0
    I_removed = sum(
        B * (2.0 * r) ** 3 / 12.0 + B * (2.0 * r) * (xc - x_bar) ** 2
        for xc in centros
    )
    I_base_net = I_gross - I_removed
    return A_base_net, I_base_net


@app.cell
def _(
    A_ab_base,
    A_net,
    V_net,
    V_net_sup,
    h_ab_total,
    h_ext_sup,
    mo,
    r,
    warnings,
    z_cg_net,
):
    warn_md = "\n\n".join(warnings) if warnings else "Aberturas dentro de los limites del machon."

    mo.md(
        f"""
        **Radio de abertura (r):** {r:.3f} m &nbsp;|&nbsp; **Altura de abertura total:** {h_ab_total:.3f} m &nbsp;|&nbsp; **Extension sobre terreno (2r):** {h_ext_sup:.3f} m

        | Magnitud | Valor |
        |---|---|
        | Area de abertura base | {A_ab_base:.4f} m2 |
        | Area neta seccion | {A_net:.3f} m2 |
        | Volumen machon | {V_net:.3f} m3 |
        | Altura del CG (desde la base) | {z_cg_net:.3f} m |
        | Volumen sobre terreno | {V_net_sup:.3f} m3 |

        {warn_md}
        """
    )
    return


@app.cell
def _(mo):
    mo.md("""
    ## 3. Cargas
    """)
    return


@app.cell
def _(
    Cs_input,
    Q_tub_input,
    V_net,
    V_net_sup,
    gamma_c_input,
    mo,
    n_pipes,
    r_pipe_input,
    z_cg_net,
    z_cg_sup,
):
    g = 9.81
    gamma_c = gamma_c_input.value  # kg/m3
    gamma_c_kN = gamma_c * g / 1000.0  # kN/m3

    W = gamma_c_kN * V_net  # kN, peso neto TOTAL (deslizamiento y volcamiento)
    W_sup = gamma_c_kN * V_net_sup  # kN, peso neto SOBRE TERRENO (sismo)

    Cs = Cs_input.value
    F_sismo = Cs * W_sup  # kN, carga sismica basada en la masa sobre terreno

    Q_tub = Q_tub_input.value  # kN, por caneria
    F_tub = n_pipes * Q_tub  # kN, total
    z_tub = r_pipe_input.value  # m, altura de aplicacion

    mo.md(
        f"""
        | Carga | Valor | Punto de aplicacion (altura desde la base) |
        |---|---|---|
        | Peso propio neto total W | {W:.2f} kN | z = {z_cg_net:.3f} m (centroide total) |
        | Peso sobre terreno W_sup | {W_sup:.2f} kN | z = {z_cg_sup:.3f} m (centroide masa ) |
        | Carga transversal total F_tub ({n_pipes} canerias) | {F_tub:.2f} kN | z = {z_tub:.3f} m |
        | Carga sismica F_sismo = Cs.W_sup | {F_sismo:.2f} kN | z = {z_cg_sup:.3f} m (centroide masa) |
        """
    )
    return F_sismo, F_tub, W, z_tub


@app.cell
def _(mo):
    mo.md("""
    ## 4. Verificaciones — dirección larga del machón (L)
    """)
    return


@app.cell
def _(
    A_base_net,
    B,
    D_emb,
    F_sismo,
    F_tub,
    I_base_net,
    L,
    W,
    factor_mov_input,
    gamma_suelo_input,
    math,
    mu,
    phi_input,
    pp_toggle_input,
    z_cg_sup,
    z_tub,
):
    # Momento de volcamiento usando z_cg_sup para F_sismo
    M_ot_suma = F_tub * z_tub + F_sismo * z_cg_sup
    M_ot_resta = abs(F_tub * z_tub - F_sismo * z_cg_sup)
    M_ot = max(M_ot_suma, M_ot_resta)

    # Momento resistente considerando masa TOTAL W
    M_r = W * (L / 2.0)

    FS_volc_suma = M_r / M_ot_suma if M_ot_suma > 0 else float("inf")
    FS_volc_resta = M_r / M_ot_resta if M_ot_resta > 0 else float("inf")
    FS_volc = min(FS_volc_suma, FS_volc_resta)

    # Resistencia al deslizamiento considerando masa TOTAL W
    Pp_total = 0.0
    if pp_toggle_input.value and D_emb > 0:
        Kp = math.tan(math.radians(45.0 + phi_input.value / 2.0)) ** 2
        Pp_total = (
            factor_mov_input.value * 0.5 * Kp
            * gamma_suelo_input.value * D_emb ** 2 * B
        )

    H_suma = F_tub + F_sismo
    H_resta = abs(F_tub - F_sismo)

    FS_desl_suma = (mu * W + Pp_total) / H_suma if H_suma > 0 else float("inf")
    FS_desl_resta = (mu * W + Pp_total) / H_resta if H_resta > 0 else float("inf")
    FS_desl = min(FS_desl_suma, FS_desl_resta)

    # Tension sobre el suelo
    e = M_ot / W if W > 0 else 0.0
    q_max = W / A_base_net + M_ot * (L / 2.0) / I_base_net
    q_min = W / A_base_net - M_ot * (L / 2.0) / I_base_net
    contacto_total = q_min >= 0
    return (
        FS_desl,
        FS_desl_resta,
        FS_desl_suma,
        FS_volc,
        FS_volc_resta,
        FS_volc_suma,
        M_ot,
        Pp_total,
        contacto_total,
        e,
        q_max,
        q_min,
    )


@app.cell
def _(
    FSD_min_input,
    FSV_min_input,
    FS_desl,
    FS_desl_resta,
    FS_desl_suma,
    FS_volc,
    FS_volc_resta,
    FS_volc_suma,
    Pp_total,
    contacto_total,
    e,
    mo,
    pp_toggle_input,
    q_max,
    q_min,
    sigma_adm_input,
):
    FSD_min = FSD_min_input.value
    FSV_min = FSV_min_input.value
    sigma_adm = sigma_adm_input.value * 9.81  # t/m2 -> kN/m2

    check_volc = "✅ Cumple" if FS_volc >= FSV_min else "❌ No cumple"
    check_desl = "✅ Cumple" if FS_desl >= FSD_min else "❌ No cumple"
    check_suelo = "✅ Cumple" if q_max <= sigma_adm else "❌ No cumple"
    check_contacto = (
        "✅ Contacto total en toda la base (q_min ≥ 0)"
        if contacto_total
        else "⚠️ q_min < 0 → tracción/despegue en un extremo. El modelo lineal simple ya no es válido "
             "sobre una base discontinua; requiere un análisis de contacto parcial aparte (fuera de este chequeo)."
    )
    pp_estado = (
        f"{Pp_total:.2f} kN (activa)" if pp_toggle_input.value else "No considerada"
    )

    mo.md(
        f"""
        ### Resumen de resultados

        | Verificación | Sismo suma | Sismo resta | Gobernante | Mínimo/Admisible | Resultado |
        |---|---|---|---|---|---|
        | FS Volcamiento | {FS_volc_suma:.2f} | {FS_volc_resta:.2f} | {FS_volc:.2f} | ≥ {FSV_min:.2f} | {check_volc} |
        | FS Deslizamiento | {FS_desl_suma:.2f} | {FS_desl_resta:.2f} | {FS_desl:.2f} | ≥ {FSD_min:.2f} | {check_desl} |

        | Magnitud | Valor |
        |---|---|
        | Presión máxima sobre el suelo q_max | {q_max:.1f} kN/m² |
        | Presión mínima sobre el suelo q_min | {q_min:.1f} kN/m² |
        | Presión admisible del suelo | {sigma_adm:.1f} kN/m² ({sigma_adm_input.value:.1f} t/m²) |
        | Excentricidad e | {e:.3f} m |
        | Resistencia por presión pasiva Pp | {pp_estado} |

        **Presión sobre el suelo:** {check_suelo}

        **Distribución de contacto:** {check_contacto}
        """
    )
    return


@app.cell
def _(mo):
    mo.md("""
    ## 5. Esquema del machón (vista L-H)
    """)
    return


@app.cell
def _(D_emb, F_sismo, F_tub, H, L, centros, np, plt, r, z_cg_sup, z_tub):
    fig, ax = plt.subplots(figsize=(7, 4.5))

    # Contorno del machon
    ax.plot([0, L, L, 0, 0], [0, 0, H, H, 0], color="black", linewidth=1.5)

    # Linea de nivel del terreno
    if D_emb > 0:
        ax.axhline(D_emb, color="sienna", linestyle=":", linewidth=1.0)
        ax.annotate("Nivel del terreno", xy=(L * 0.02, D_emb), color="sienna", fontsize=7, va="bottom")

    # Aberturas: rectangulo inferior + semicirculo superior
    for xx in centros:
        ax.plot(
            [xx - r, xx - r, xx + r, xx + r],
            [0, r, r, 0],
            color="firebrick",
            linewidth=1.2,
        )
        theta = np.linspace(0, np.pi, 100)
        xs = xx + r * np.cos(theta)
        ys = r + r * np.sin(theta)
        ax.plot(xs, ys, color="firebrick", linewidth=1.2)

    # Altura de aplicacion de la carga transversal de las canerias
    ax.axhline(z_tub, color="steelblue", linestyle="--", linewidth=0.8)
    ax.annotate(
        f"F_tub = {F_tub:.1f} kN\n(z = {z_tub:.2f} m)",
        xy=(L * 0.02, z_tub),
        color="steelblue",
        fontsize=8,
        va="bottom",
    )

    # Centro de gravedad de masa sobre terreno (altura de aplicacion del sismo)
    ax.plot(L / 2, z_cg_sup, marker="x", color="darkgreen")
    ax.annotate(
        f"CG sup, z = {z_cg_sup:.2f} m\nF_sismo = {F_sismo:.1f} kN",
        xy=(L / 2, z_cg_sup),
        color="darkgreen",
        fontsize=8,
        ha="left",
        va="bottom",
    )

    ax.set_xlim(-0.1, L + 0.1)
    ax.set_ylim(-0.1, H + 0.1)
    ax.set_aspect("equal")
    ax.set_xlabel("L (m)")
    ax.set_ylabel("H (m)")
    ax.set_title("Vista L-H del machon, con aberturas para las dos canerias")
    fig
    return


@app.cell
def _(mo):
    mo.md("""
    ## 6. Diagrama de presión de contacto sobre el suelo
    """)
    return


@app.cell
def _(A_base_net, I_base_net, L, M_ot, W, centros, plt, r):
    fig2, ax2 = plt.subplots(figsize=(6.5, 2.8))

    def q_at(x):
        return W / A_base_net + M_ot * (x - L / 2.0) / I_base_net

    bordes = sorted(centros)
    segmentos = []
    x_prev = 0.0
    for bor in bordes:
        segmentos.append((x_prev, bor - r))
        x_prev = bor + r
    segmentos.append((x_prev, L))

    q_vals = []
    for x0, x1_ in segmentos:
        if x1_ > x0:
            ys_seg = [q_at(x0), q_at(x1_)]
            ax2.fill_between([x0, x1_], 0, ys_seg, color="tan", alpha=0.6)
            ax2.plot([x0, x1_], ys_seg, color="saddlebrown", linewidth=1.5)
            q_vals.extend(ys_seg)

    for cen in centros:
        ax2.axvspan(cen - r, cen + r, color="lightgray", alpha=0.5)

    ax2.set_xlim(0, L)
    top = max(q_vals) * 1.25 if q_vals and max(q_vals) > 0 else 1.0
    bottom = min(0, min(q_vals) * 1.25) if q_vals else 0.0
    ax2.set_ylim(bottom, top)
    ax2.invert_yaxis()
    ax2.set_xlabel("L (m)")
    ax2.set_ylabel("q (kN/m²)")
    ax2.set_title("Presión de contacto sobre el suelo (base discontinua por aberturas)")
    fig2
    return


@app.cell
def _(math):
    def calc_fsd(
        L, H, B, r, sep, n_pipes, Q_tub, Cs, gamma_c, mu,
        pp_enabled=False, D_emb=0.0, gamma_suelo=18.0, phi_deg=32.0, factor_mov=1.0,
    ):
        A_rect = 2.0 * r * r
        A_semi = math.pi * r ** 2 / 2.0
        A_ab_base = A_semi + A_rect
        A_gross = L * H
        A_net = A_gross - n_pipes * A_ab_base
        if A_net <= 0:
            return float("nan")
        V_net = A_net * B

        # Extension de abertura sobre terreno (2*r sobre cota D_emb)
        D_emb_eff = min(D_emb, H)
        H_sup = max(0.0, H - D_emb_eff)
        A_gross_sup = L * H_sup

        h_sup_ab = min(H_sup, 2.0 * r)
        A_ab_sup = (2.0 * r) * h_sup_ab
        A_net_sup = max(0.0, A_gross_sup - n_pipes * A_ab_sup)
        V_net_sup = A_net_sup * B

        gamma_c_kN = gamma_c * 9.81 / 1000.0
        W_total = gamma_c_kN * V_net
        W_sup = gamma_c_kN * V_net_sup

        F_sismo = Cs * W_sup
        F_tub = n_pipes * Q_tub
        H_suma = F_tub + F_sismo
        H_resta = abs(F_tub - F_sismo)
        H_total = max(H_suma, H_resta)

        Pp_total = 0.0
        if pp_enabled and D_emb_eff > 0:
            Kp = math.tan(math.radians(45.0 + phi_deg / 2.0)) ** 2
            Pp_total = factor_mov * 0.5 * Kp * gamma_suelo * D_emb_eff ** 2 * B

        if H_total <= 0:
            return float("inf")
        return (mu * W_total + Pp_total) / H_total


    return (calc_fsd,)


@app.cell
def _(mo):
    B_range_input = mo.ui.range_slider(start=0.2, stop=2.0, step=0.05, value=[0.4, 1.5], label="Rango B (m)")
    H_range_input = mo.ui.range_slider(start=0.3, stop=4.0, step=0.05, value=[0.8, 3.0], label="Rango H (m)")
    mo.hstack([B_range_input, H_range_input])
    return B_range_input, H_range_input


@app.cell
def _(
    B_range_input,
    Cs_input,
    D_emb_input,
    FSD_min_input,
    H_range_input,
    L_input,
    Q_tub_input,
    ancho_abertura_input,
    calc_fsd,
    factor_mov_input,
    gamma_c_input,
    gamma_suelo_input,
    mu,
    n_pipes_input,
    np,
    phi_input,
    plt,
    pp_toggle_input,
    sep_input,
):
    B_grid = np.linspace(*B_range_input.value, 60)
    H_grid = np.linspace(*H_range_input.value, 60)
    BB, HH = np.meshgrid(B_grid, H_grid)

    r_val = ancho_abertura_input.value / 2.0
    n_pipes_val = int(n_pipes_input.value)

    FSD_grid = np.vectorize(
        lambda B, H: calc_fsd(
            L_input.value, H, B, r_val, sep_input.value, n_pipes_val,
            Q_tub_input.value, Cs_input.value, gamma_c_input.value, mu,
            pp_enabled=pp_toggle_input.value,
            D_emb=D_emb_input.value,
            gamma_suelo=gamma_suelo_input.value,
            phi_deg=phi_input.value,
            factor_mov=factor_mov_input.value,
        )
    )(BB, HH)

    FS_min = FSD_min_input.value

    fig3, ax3 = plt.subplots(figsize=(6.5, 5))
    cf = ax3.contourf(
        BB, HH, FSD_grid, levels=20, cmap="RdYlGn",
        vmin=0, vmax=max(FS_min * 2, np.nanmax(FSD_grid)),
    )
    cs = ax3.contour(BB, HH, FSD_grid, levels=[FS_min], colors="black", linewidths=2)
    ax3.clabel(cs, fmt=f"FS={FS_min:.2f}")
    plt.colorbar(cf, ax=ax3, label="FS deslizamiento")
    ax3.set_xlabel("B (m)")
    ax3.set_ylabel("H (m)")
    ax3.set_title("Sensibilidad de FS deslizamiento — B vs H")
    fig3
    return


if __name__ == "__main__":
    app.run()
