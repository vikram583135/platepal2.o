import { Card, CardContent, CardHeader, CardTitle } from '@/packages/ui/components/card'
import { Badge } from '@/packages/ui/components/badge'
import { Flame, AlertTriangle } from 'lucide-react'

interface NutritionInfoProps {
  calories?: number | null
  macros?: {
    protein?: number
    carbs?: number
    fat?: number
    fiber?: number
    sugar?: number
  } | null
  allergens?: string[] | null
}

export default function NutritionInfo({ calories, macros, allergens }: NutritionInfoProps) {
  if (!calories && !macros && (!allergens || allergens.length === 0)) {
    return null
  }

  return (
    <Card className="mt-4">
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <Flame className="w-5 h-5" />
          Nutrition Information
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Calories */}
        {calories && (
          <div className="flex items-center justify-between p-3 bg-orange-50 rounded-lg">
            <span className="font-medium">Calories</span>
            <span className="text-2xl font-bold text-orange-600">{calories}</span>
          </div>
        )}

        {/* Macros */}
        {macros && (macros.protein || macros.carbs || macros.fat) && (
          <div>
            <h4 className="font-semibold mb-2">Macronutrients (per serving)</h4>
            <div className="grid grid-cols-3 gap-3">
              {macros.protein !== undefined && (
                <div className="text-center p-2 bg-blue-50 rounded">
                  <div className="text-xs text-gray-600">Protein</div>
                  <div className="font-bold text-blue-600">{macros.protein}g</div>
                </div>
              )}
              {macros.carbs !== undefined && (
                <div className="text-center p-2 bg-green-50 rounded">
                  <div className="text-xs text-gray-600">Carbs</div>
                  <div className="font-bold text-green-600">{macros.carbs}g</div>
                </div>
              )}
              {macros.fat !== undefined && (
                <div className="text-center p-2 bg-yellow-50 rounded">
                  <div className="text-xs text-gray-600">Fat</div>
                  <div className="font-bold text-yellow-600">{macros.fat}g</div>
                </div>
              )}
            </div>
            {(macros.fiber !== undefined || macros.sugar !== undefined) && (
              <div className="grid grid-cols-2 gap-3 mt-2">
                {macros.fiber !== undefined && (
                  <div className="text-center p-2 bg-purple-50 rounded">
                    <div className="text-xs text-gray-600">Fiber</div>
                    <div className="font-bold text-purple-600">{macros.fiber}g</div>
                  </div>
                )}
                {macros.sugar !== undefined && (
                  <div className="text-center p-2 bg-pink-50 rounded">
                    <div className="text-xs text-gray-600">Sugar</div>
                    <div className="font-bold text-pink-600">{macros.sugar}g</div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Allergens */}
        {allergens && allergens.length > 0 && (
          <div>
            <h4 className="font-semibold mb-2 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-red-500" />
              Allergens
            </h4>
            <div className="flex flex-wrap gap-2">
              {allergens.map((allergen, index) => (
                <Badge key={index} variant="destructive" className="text-xs">
                  {allergen.charAt(0).toUpperCase() + allergen.slice(1)}
                </Badge>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

