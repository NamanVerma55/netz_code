import math
def quadratic_roots(a, b, c):
    """Calculate the roots of a quadratic equation ax^2 + bx + c = 0."""
    if a == 0:
        return "Not a quadratic equation (a cannot be 0)"
    
    discriminant = b**2 - 4*a*c  # Calculate the discriminant
    
    if discriminant > 0:
        # Two real and distinct roots
        root1 = (-b + math.sqrt(discriminant)) / (2*a)
        root2 = (-b - math.sqrt(discriminant)) / (2*a)
        return root1, root2
    elif discriminant == 0:
        # One real and repeated root
        root = -b / (2*a)
        return root,
    else:
        # Complex roots
        real_part = -b / (2*a)
        imaginary_part = math.sqrt(abs(discriminant)) / (2*a)
        return (real_part + imaginary_part * 1j, real_part - imaginary_part * 1j)