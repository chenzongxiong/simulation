import numpy as np
import matplotlib.pyplot as plt


def foo(delta, alpha):
    f = 1 - (1-np.exp(-alpha))/np.exp(-alpha) * delta
    t1 = - np.log(f[f > 0])
    t2 = alpha[f > 0]
    n = t1 / t2
    print("max delta: {:.3f}, max_alpha: {:.3f}, shape: {}, sum: {:.3f}".format(
        delta[-1], alpha[-1], t1.shape[-1], n[1:].sum()))
    return t1.shape[-1], n[1:].sum()

DELTA_LIST = [0.1 * (i + 1) for i in range(10)] + [2 * (i + 1) for i in range(10)]
ALPHA_LIST = [0.1 * (i + 1) for i in range(10)] + [(i + 1) for i in range(10)]

d_len = len(DELTA_LIST)
a_len = len(ALPHA_LIST)
heatmap_s = np.zeros((a_len, d_len))
heatmap_v = np.zeros((a_len, d_len))

for i, a in enumerate(ALPHA_LIST):
    for j, d in enumerate(DELTA_LIST):
        alpha = np.linspace(1e-5, a, 1000)
        delta = np.linspace(1e-5, d, 1000)
        v, s = foo(delta, alpha)

        heatmap_v[a_len-1-i][j] = v
        heatmap_s[a_len-1-i][j] = s


fig, (ax1, ax2) = plt.subplots(1, 2)

fig.set_figheight(30)
fig.set_figwidth(30)


def plot(ax, value, threshold, title=''):
    im = ax.imshow(value)
    ax.figure.colorbar(im, ax=ax)
    ax.set_xlabel("delta")
    ax.set_ylabel("alpha")
    ax.set_xticks(np.arange(d_len))
    ax.set_yticks(np.arange(a_len))
    ax.set_xticklabels(["{:.1f}".format(i) for i in DELTA_LIST])
    ax.set_yticklabels(["{:.1f}".format(i) for i in ALPHA_LIST[::-1]])
    for i in range(a_len):
        for j in range(d_len):
            if value[i][j] >= threshold and ALPHA_LIST[i] > 0.1 and DELTA_LIST[j] > 0.1:
                print("delta: {:.2f}, alpha: {:.2f}, value: {:.2f}".format(DELTA_LIST[j], ALPHA_LIST[i], value[i][j]))
                text = ax.text(j, i, '*', ha="center", va="center", color="w")
    ax.set_title(title)


plot(ax1, heatmap_v, threshold=700, title="percentage")
plot(ax2, heatmap_s, threshold=3000, title="total stocks")

fig.tight_layout()

plt.show()
fig.savefig("./agentn-analysis-heatmap.png", dpi=400)
