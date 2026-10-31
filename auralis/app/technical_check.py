"""Bounded deterministic arithmetic checks, not design or standards certification."""
import math
from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import Literal

Case = Literal['gravity_load','bend_allowance','plate_stiffness_ratio','three_phase_current']

class TechnicalCheckRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    case: Case
    values: dict[str, float] = Field(min_length=2, max_length=4)
    claimed_result: float | None = None
    @model_validator(mode='after')
    def bound(self):
        if self.claimed_result is not None and (not math.isfinite(self.claimed_result) or abs(self.claimed_result) > 1e12):
            raise ValueError('Claimed result must be a finite number within the supported range.')
        for val in self.values.values():
            if isinstance(val, bool) or not math.isfinite(val) or abs(val) > 1e10:
                raise ValueError('All input values must be finite numbers within the supported range.')
        return self

SPECS = {
    'gravity_load': {
        'name':'Equipment gravitational load', 'unit':'N',
        'fields':{'mass_kg':(0.001, 1e7), 'gravity_m_s2':(0.01, 100)},
        'formula':'F = m × g',
        'note':'Static gravitational force only; excludes vibration, dynamic effects, supports and safety factors.'
    },
    'bend_allowance': {
        'name':'Sheet-metal bend allowance', 'unit':'mm',
        'fields':{'angle_deg':(0.01, 360), 'inside_radius_mm':(0, 1e4), 'thickness_mm':(0.001, 1e4), 'k_factor':(0, 0.5)},
        'formula':'BA = (π × angle / 180) × (R + K × t)',
        'note':'Idealized developed-length estimate. Validate K-factor against material, tooling, bend method and supplier trials.'
    },
    'plate_stiffness_ratio': {
        'name':'Ideal plate-bending stiffness ratio', 'unit':'×',
        'fields':{'thickness_before_mm':(0.001, 1e4), 'thickness_after_mm':(0.001, 1e4)},
        'formula':'D₂ / D₁ = (t₂ / t₁)³',
        'note':'Assumes identical elastic material properties, Poisson ratio and panel geometry; does not predict buckling or complete-assembly stiffness.'
    },
    'three_phase_current': {
        'name':'Balanced three-phase line current', 'unit':'A',
        'fields':{'real_power_w':(0.01, 1e10), 'line_voltage_v':(0.01, 1e8), 'power_factor':(0.01, 1)},
        'formula':'I = P / (√3 × V_LL × PF)',
        'note':'Assumes a balanced three-phase load and real power P. Does not size protection, cabling or equipment.'
    },
}

def check_calculation(request: TechnicalCheckRequest):
    spec=SPECS[request.case]
    if set(request.values) != set(spec['fields']):
        from fastapi import HTTPException
        raise HTTPException(422, f"This case requires exactly: {', '.join(spec['fields'])}.")
    for key, (low, high) in spec['fields'].items():
        v=request.values[key]
        if not low <= v <= high:
            from fastapi import HTTPException
            raise HTTPException(422, f'{key} must be between {low} and {high}.')
    v=request.values
    if request.case=='gravity_load':
        result=v['mass_kg']*v['gravity_m_s2']
    elif request.case=='bend_allowance':
        result=math.radians(v['angle_deg'])*(v['inside_radius_mm']+v['k_factor']*v['thickness_mm'])
    elif request.case=='plate_stiffness_ratio':
        result=(v['thickness_after_mm']/v['thickness_before_mm'])**3
    else:
        result=v['real_power_w']/(math.sqrt(3)*v['line_voltage_v']*v['power_factor'])
    if not math.isfinite(result) or result>1e12:
        from fastapi import HTTPException
        raise HTTPException(422,'The result exceeds the supported numeric range.')
    claimed=request.claimed_result
    # 1% relative tolerance and tiny absolute floor are UX comparison heuristics, not engineering pass/fail standards.
    relative_error=abs(claimed-result)/max(abs(result),1e-9) if claimed is not None else None
    comparison='not_supplied' if claimed is None else ('within_1_percent' if relative_error<=0.01 else 'different')
    return {
        'case':request.case, 'name':spec['name'], 'formula':spec['formula'],
        'result':round(result,9), 'unit':spec['unit'], 'inputs':v,
        'claimed_result':claimed, 'relative_error_percent':round(relative_error*100,4) if relative_error is not None else None,
        'comparison':comparison, 'interpretation':spec['note'],
        'warning':'Arithmetic check only. Not an assessment of material adequacy, code compliance, installation safety, or personal competence.',
        'source':'deterministic_formula',
    }
