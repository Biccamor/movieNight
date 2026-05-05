from fastapi import APIRouter

router = APIRouter(prefix="/metadata", tags=["Metadata"])

@router.get("/preferences-options")
async def get_preferences_options():
    """
    Returns available movie genres and eras for the preferences selection.
    """
    vibes = [
        "AMBITIOUS",
        "PIZZA_CHILL",
        "MIND_BENDER",
        "ADRENALINE",
        "DATE_NIGHT",
        "DEEP_FEELS",
        "LAUGH_RIOT",
        "SPINE_CHILLING",
        "NOSTALGIA",
        "INSPIRING",
        "EPIC_JOURNEY",
        "GUILTY_PLEASURE"
    ]
    
    eras = [
        'Klasyka (przed 80.)',
        'Lata 80.',
        'Lata 90.',
        'Lata 00.',
        'Lata 10.',
        'Nowości (Lata 20.)'
    ]
    
    return {
        "vibes": vibes,
        "eras": eras
    }
