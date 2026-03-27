from __future__ import annotations

import decimal
from dataclasses import dataclass

D = decimal.Decimal


def money(v: float | int | str | decimal.Decimal) -> decimal.Decimal:
    return D(str(v)).quantize(D("0.01"))


@dataclass(frozen=True)
class TaxSplit:
    cgst_amount: decimal.Decimal
    sgst_amount: decimal.Decimal
    total_tax: decimal.Decimal


def split_gst(amount_excl_tax: decimal.Decimal, cgst_rate: decimal.Decimal, sgst_rate: decimal.Decimal) -> TaxSplit:
    cgst = (amount_excl_tax * cgst_rate / D("100")).quantize(D("0.01"))
    sgst = (amount_excl_tax * sgst_rate / D("100")).quantize(D("0.01"))
    return TaxSplit(cgst, sgst, (cgst + sgst).quantize(D("0.01")))


def exclusive_base_from_inclusive(
    amount_incl_tax: decimal.Decimal, cgst_rate: decimal.Decimal, sgst_rate: decimal.Decimal
) -> decimal.Decimal:
    total_rate = (cgst_rate + sgst_rate) / D("100")
    if total_rate == 0:
        return amount_incl_tax
    return (amount_incl_tax / (D("1.0") + total_rate)).quantize(D("0.01"))

