# 出典と主張の対応

作成日：2026-11-16。本文・台本・図は新規作成。文献の本文を翻訳して読み上げる動画ではなく、独立に構成した入門解説である。論文の図版、講義映像、人物写真は使用していない。以下のページ番号は文献自身の番号を優先する。

## R1：相互法則と L 関数

Matthew Emerton, *Langlands Reciprocity: L-Functions, Automorphic Forms, and Diophantine Equations*.
https://www.math.uchicago.edu/~emerton/pdffiles/reciprocity.pdf

参照箇所：導入、Artin L 関数・motivic L 関数、保型 L 関数と相互法則の各節。動画では、算術側と保型側で独立に定義される局所因子を比較するという構想、ガロア表現の役割の確認に用いた。

## R2：一般の群と関手性

A. W. Knapp, *Introduction to the Langlands Program*, Proceedings of Symposia in Pure Mathematics 61 (1997), 245–302.
https://math.stanford.edu/~conrad/JLseminar/refs/Knappintro.pdf

参照箇所：§§1–5（局所体、類体論、L 関数）、§7（保型形式）、§§8–10（GLn、L 群、関手性）。動画の矢印は見取り図であり、群の任意の準同型から保型移送を主張してはいない。対称二乗移送は古典的に知られた例だが、動画ではその存在証明を扱わない。

## R3：楕円曲線の具体例

LMFDB, elliptic curve **32.a3**（Cremona label **32a2**）.
https://www.lmfdb.org/EllipticCurve/Q/32/a/3

用いたデータ：最小方程式 y²=x³−x、導手32、判別式64、対応する保型形式32.2.a.a。従って良い素数は奇素数。点の個数はページから転記せず、同梱コードで全候補を数え直した。

## R4：モジュラー形式とモジュラー性

Andrew Sutherland, MIT 18.783 *Elliptic Curves*, Lecture 24, 17 May 2021.
https://ocw.mit.edu/courses/18-783-elliptic-curves-spring-2021/17d693389d2ad0a5e0627da111a08428_MIT18_783S21_Slides24.pdf

参照箇所：スライド2（モジュラー性定理）、3–5（変換則、正則性、カスプ条件）、8–10（固有形式、新形式）、後半のL関数とモジュラー性。変換則だけをモジュラー形式の完全な定義とはしていない。

1995年の半安定の場合と2001年の有理数上の一般の場合を区別した。歴史記述を「ワイルズ一人が全場合を証明した」とはしていない。

## R5：対応する新形式の係数

LMFDB, newform orbit **32.2.a.a**.
https://www.lmfdb.org/ModularForm/GL2/Q/holomorphic/32/2/a/a/

用いたデータ：重さ2、レベル32、係数体Q、

```tex
f(z)=\eta(4z)^2\eta(8z)^2
    =q\prod_{n\ge1}(1-q^{4n})^2(1-q^{8n})^2
    =q-2q^5-3q^9+6q^{13}+2q^{17}+\cdots.
```

画面の係数はこのデータと照合し、同梱コードでも積を整数演算で独立に展開した。

## R6：p進局所体の GLn

Michael Harris, *On the local Langlands correspondence*, ICM 2002 proceedings / arXiv:math/0304324.
https://arxiv.org/abs/math/0304324

Harris–TaylorおよびHenniartによるp進局所体上のGLnの対応を確認するために用いた。一般の局所対応のパラメータは、単なる有限体上の点数ではなく、Weil–Deligne型のデータを含む。

## R7：数体の大域的相互法則の条件

Ana Caraiani and Sug Woo Shin, *Recent progress on Langlands reciprocity for GLn: Shimura varieties and beyond*, arXiv:2311.13382.
https://arxiv.org/abs/2311.13382

参照箇所：導入と、ガロア表現・保型表現の条件を述べる部分。2023年のサーベイであり、2026年時点の成果を網羅した一覧として使ってはいない。「全ガロア表現」と「全保型形式」の無条件な一対一対応を主張しないための確認資料。

## R8：関数体上の GLn

Laurent Lafforgue, *La correspondance de Langlands sur les corps de fonctions*, 4 October 1999, Jussieu seminar abstract.
https://www.imj-prg.fr/tn/STN/99/resume-Lafforgue.html

著者による説明。有限体上の曲線の関数体のGLnについて、適切な既約ℓ進表現と尖点的保型表現の対応を扱う。動画では基礎体を省略して「GLnは全部解決」とは述べない。

## R9：幾何学版の著者公開ページ

D. Arinkin, D. Beraldo, J. Campbell, L. Chen, J. Faergeman, D. Gaitsgory, K. Lin, S. Raskin, N. Rozenblyum, *Proof of the geometric Langlands conjecture* project.
https://people.mpim-bonn.mpg.de/gaitsgde/GLC/

著者公開ページは対象を **categorical, unramified** と明記している。算術的な数体版全体と同じ主張ではない。

## R10：幾何学版の設定の説明

Dennis Gaitsgory, *On the Proof of the Geometric Langlands Correspondance*, IHES, 2024.
https://www.ihes.fr/en/gaitsgory-glc/

標数0のde Rham設定など、証明の対象となる設定を確認するために用いた。最新成果の網羅的な紹介は本動画の目的ではない。

## C1：この制作物での独立計算

`verify_examples.py` は次の二つを別々に計算する。

1. 全座標対を調べ、無限遠点を加えて #E(Fp) を求める。
2. エータ積の無限積を指定次数で打ち切り、厳密な整数係数の多項式演算で展開する。

199以下の45個の奇素数について aₚ=bₚ を確認した。結果は `verification.json` に保存した。**有限個の照合は、全ての素数についての定理の証明ではない。**

## C2：線形代数の説明

2次元ベクトル空間の対称二乗には、基底を x², xy, y² と取れる。元の作用が固有値α,βを持つ対角行列なら、対称二乗での固有値はα²,αβ,β²。この計算と、保型移送の存在証明は別である。

## 正規化・省略事項

- 楕円曲線からのガロア表現は有理テイト加群上の作用を採用した。良い素数p≠ℓにおける算術的フロベニウスに対して、トレースはaₚ、行列式はp。
- `det(I−AₚT)` は局所因子の分母を記述する多項式。通常の特性多項式 `det(TI−Aₚ)` とは変数の置き方が異なる。
- 画面の `L(E,s)=L(f,s)` は重さ2の古典的モジュラー形式の算術的正規化。同じ式を、ユニタリ正規化した一般の保型表現へ無修正で流用しない。
- ガロア表現の連続性、幾何学的条件、保型側の代数性などの仮定、L群、同値関係、局所との整合性を指定して、初めて精密な対応の主張になる。
- 楕円曲線と新形式の対応を逆向きに読む際、曲線一つとの無条件な一対一対応ではなく、適切な条件下での同種写像類を考える。
- ガロア側の有限次元表現と保型側の一般に無限次元の表現を、同じサイズの行列同士とは説明していない。
- 本動画は証明講義ではない。テイト加群、保型表現の空間、L群の構成を厳密に学ぶには上記文献が必要。

## 今回の音声とキャラクター

音声は eSpeak 1.48.15 の音素入力で合成。AquesTalk・VOICEVOXは使用していない。キャラクター画像は本動画向けに新規生成したライムとマサリ。技術資料とクレジットは `CREDITS.md` を参照。

今回の改稿時にも R3・R5 の公開データと R9・R10 の公開ページを確認した。過去の資料は2026年の全成果を網羅するために用いたものではない。
