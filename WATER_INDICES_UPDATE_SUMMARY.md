# Water Stability Indices API Update Summary

## Overview
The `api/calculate-water-analysis-with-recommendations` endpoint has been updated to include additional water stability indices based on the formulae from the Water Stability Indices documents.

## New Indices Added

### 1. Puckorius Scaling Index (PSI)
- **Formula**: PSI = 2 × pHe - pHs
- **Where**: pHe = 1.465 + Log10(Alk as CaCO3) + 4.54
- **Interpretation**:
  - PSI < 4.5: Water has a tendency to scale
  - PSI 4.5 - 6.5: Water is in optimal range (no corrosion or scaling)
  - PSI > 6.5: Water has a tendency to corrode

### 2. Langelier Ratio (LR)
- **Formula**: LR = [epm Cl + epm SO4] / [epm HCO3 + epm CO3]
- **Where**:
  - epm Cl = Chloride as Cl / 35.5
  - epm SO4 = Sulphate as SO4 / 96
  - Molar Alkalinity, [Alk] = Total Alk as CaCO3 / 100
  - epm HCO3 and epm CO3 calculated from carbonate speciation using exact equilibrium constants
- **Equilibrium Constants (Temperature-Dependent):**
  - K1 = 10^-(3404.71/Temp + 0.032786 × Temp - 14.8435)
  - K2 = 10^-(2902.39/Temp + 0.02379 × Temp - 6.498)
- **Carbonate Speciation:**
  - [H+] = 10^-pH
  - αHCO3 = [H+] × K1 / ([H+]² + [H+] × K1 + K1 × K2)
  - αCO3 = K1 × K2 / ([H+]² + [H+] × K1 + K1 × K2)
  - epm HCO3 = [Alk] × αHCO3
  - epm CO3 = [Alk] × αCO3
- **Interpretation (Exact from Image):**
  - LR < 0.8: Chlorides and sulfate probably will not interfere with natural film formation
  - LR 0.8 < 1.2: Chlorides and sulfates may interfere with natural film formation. Higher than desired corrosion rates might be anticipated.
  - LR > 1.2: The tendency towards high corrosion rates of a local type should be expected as the index increases

## Enhanced LSI Calculation
The LSI calculation has been updated to use the more accurate formulae from the document:
- **Formula**: pHs = 9.3 + A + B - C - D
- **Where**:
  - A = (Log10(TDS) - 1) / 10
  - B = -13.12 × Log10(Temp (°C) + 273) + 34.55
  - C = Log10(Ca as CaCO3) - 0.4
  - D = Log10(Alk as CaCO3)

## New Parameters
- **sulphate**: Sulphate concentration in ppm (required for LR calculation)

## Updated Response Structure
The API response now includes:
```json
{
  "calculation": {
    "lsi": 0.04,
    "rsi": 7.42,
    "ls": 0.33,
    "psi": 8.90,
    "lr": 2.0,
    "stability_score": 36.0,
    "lsi_status": "Near Balance",
    "rsi_status": "Corrosion Significant",
    "ls_status": "Moderate",
    "psi_status": "Water has a tendency to corrode",
    "lr_status": "The tendency towards high corrosion rates of a local type should be expected as the index increases",
    "overall_status": "Moderate"
  },
  "recommendations": [...]
}
```

**Note**: All status descriptions now match exactly with the interpretation tables from the Water Stability Indices images.

## New Recommendations
The system now generates dynamic recommendations based on:
- **PSI status**: Scaling or corrosion prevention measures
- **LR status**: Chloride/sulfate interference control measures
- **Sulphate levels**: Treatment recommendations for high sulphate

## Enhanced Scoring System
The overall stability assessment now considers all five indices:
- LSI (Langelier Saturation Index)
- RSI (Ryznar Stability Index)
- LS (Larson-Skold Index)
- PSI (Puckorius Scaling Index)
- LR (Langelier Ratio)

## Technical Improvements
- Added proper mathematical constants for carbonate equilibrium calculations
- Improved temperature dependency handling
- Enhanced error handling for edge cases
- Added comprehensive Swagger documentation
- Updated status determination logic for all indices

## Backward Compatibility
The API maintains backward compatibility while adding new functionality. Existing clients will continue to work and receive the additional data.

## Usage Example
```bash
POST /api/calculate-water-analysis-with-recommendations/
{
  "ph": 7.5,
  "tds": 300,
  "total_alkalinity": 150,
  "hardness": 200,
  "chloride": 50,
  "temperature": 25,
  "sulphate": 75
}
```

## Files Modified
- `api/views.py`: Updated the main calculation function
- Added comprehensive Swagger documentation
- Enhanced recommendation generation logic
