# Reprezentace realných čísel

Vaším úkolem je vytvořit algoritmus, který ze vstupu načte 32-bitové číslo v binární formě specifikace [IEEE-754](https://www.h-schmidt.net/FloatConverter/IEEE754.html)
a provede konverzy do soustavy desítkové. Navíc program vypíše, jak by takový převod vypadal.

## Formát výstupu je následující:
<code><pre class="fmt">
(-1)^s * 2^(E - 127) * (1 + Q) = X
</pre></code>

Významy jednotlivých proměnných lze nalézt [zde](https://cs.wikipedia.org/wiki/IEEE_754#Z.C3.A1kladn.C3.AD_p.C5.99esnost_.28single.2C_binary32.29).

**Reálná čísla**, která se objeví na výstupu, budou zaokrouhlena na **8** desetinných míst, tzn., že číslo
`1.00000005984651` bude vypsáno jako `1.00000006`.

## Ukázka vstupu:
<code><pre class="fmt">
10111111100000000000000000000000
01000001000010000000000000000000
</pre></code>

## Ukázka výstupu:
<code><pre class="fmt">
(-1)^1 * 2^(127 - 127) * (1 + 0.00000000) = -1.00000000
(-1)^0 * 2^(130 - 127) * (1 + 0.06250000) = 8.50000000
</pre></code>

#### Požadované sady: `sada-1`, `sada-2`
