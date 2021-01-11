import pandas as pd
import numpy as np
from .models import *
import random
from decimal import Decimal
import re
###################################################################

###################################################################
"""
Eventos
"""

def modifyEvento(user, eventos):
    if eventos != None:
        for evento in eventos:
            if evento != {}:
                changefrecuencia = Evento_User.objects.get(User=user.id, Evento=evento['Evento_id'])
                Evento_User.objects.filter(User=user.id, Evento=evento['Evento_id']).update(Frecuencia=changefrecuencia.Frecuencia - 1)
    
def eventoAfecta(user, eventos):
    afectaList = []

    if eventos != None:
        for evento in eventos:
            if evento != {}:
                afecta_evento = Evento_Afecta.objects.filter(Evento=evento['Evento_id'])
                for afecta in afecta_evento:
                    tipoAfecta = afectaInversion(afecta, user)
                    if tipoAfecta:
                        duracion = Periodo.objects.filter(TipoPeriodo=afecta.Periodo).first()
                        afecta_usuario = Afecta_user(User=user, Descripcion=evento["Descripcion"], Afecta=afecta.Afecta, TurnosEsperar=duracion.Turnos, TurnosRestante=duracion.Turnos, Cantidad=afecta.Cantidad, Duracion=afecta.Duracion)
                        afecta_usuario.save()
                        afectaList.append(afecta_usuario.id)
    return afectaList

def getAfectaEvento(response):

    for i in response:
        if i != {}:
            i['Afecta'] = []
            evento = Evento.objects.filter(id = i["Evento_id"]).first()
            afectas = Evento_Afecta.objects.filter(Evento = evento)
            for afecta in afectas:
                periodo = str(afecta.Periodo)
                if afecta.Periodo.Turnos < 0:
                    periodo = "Exclusivo"
                duracion = afecta.Duracion
                if afecta.Duracion > 1000:
                    duracion = "Infinito"
                i['Afecta'].append({"Afecta": afecta.Afecta.TipoAfect, "Cantidad": afecta.Cantidad, "Periodo":periodo, "Duracion":duracion})


def verificarRequisitos(id, turno, flag_tipo):
    if(flag_tipo == 'Pregunta'):
        requisitos = Preguntas_Requisitos.objects.filter(Preguntas_id = id)
    else:
        requisitos = Evento_Requisitos.objects.filter(Evento = id)
    if not requisitos:
        return True
    else:
        for requisito in requisitos:
            req = str(requisito.Requisito)
            cant = str(requisito.Cantidad)
            if (req == 'Felicidad'):
                if(cant[0] == '>'):
                    if(turno.Felicidad > int(cant.split('>')[1])):
                        pass
                    else:
                        return False
                elif(cant[0] == '<'):
                    if(turno.Felicidad < int(cant.split('<')[1])):
                        pass
                    else:
                        return False
                elif(cant.find('-') > 0):
                    if ((turno.Felicidad >= int(cant.split('-')[0])) and (turno.Felicidad <= int(cant.split('-')[1]))):
                        pass
                    else:
                        return False
                elif(cant[0] == '='):
                    if (turno.Felicidad == int(cant.split('=')[1]) ):
                        pass
                    else:
                        return False
                        
            elif (req == 'Ingresos'):
                if(cant[0] == '>'):
                    if(turno.Ingresos > int(cant.split('>')[1])):
                        pass
                    else:
                        return False
                elif(cant[0] == '<'):
                    if(turno.Ingresos < int(cant.split('<')[1])):
                        pass
                    else:
                        return False
                elif(cant[0] == '='):
                    if(turno.Ingresos < int(cant.split('=')[1])):
                        pass
                    else:
                        return False
                elif(cant.find('-') > 0):
                    if ((turno.Ingresos >= int(cant.split('-')[0])) and (turno.Ingresos <= int(cant.split('-')[1]))):
                        pass
                    else:
                        return False
                
            elif (req == 'NumeroTurnos'):
                if(cant[0] == '>'):
                    if(turno.NumeroTurnos > int(cant.split('>')[1])):
                        pass
                    else:
                        return False
                elif(cant[0] == '<'):
                    if(turno.NumeroTurnos < int(cant.split('<')[1])):
                        pass
                    else:
                        return False
                elif(cant[0] == '='):
                    if(turno.NumeroTurnos < int(cant.split('=')[1])):
                        pass
                    else:
                        return False
                elif(cant.find('-') > 0):
                    if ((turno.NumeroTurnos >= int(cant.split('-')[0])) and (turno.NumeroTurnos <= int(cant.split('-')[1]))):
                        pass
                    else:
                        return False
            elif (req == 'DineroEfectivo'):
                if(cant[0] == '>'):
                    if(turno.NumeroTurnos > int(cant.split('>')[1])):
                        pass
                    else:
                        return False
                elif(cant[0] == '<'):
                    if(turno.NumeroTurnos < int(cant.split('<')[1])):
                        pass
                    else:
                        return False
                elif(cant[0] == '='):
                    if(turno.NumeroTurnos < int(cant.split('=')[1])):
                        pass
                    else:
                        return False
                elif(cant.find('-') > 0):
                    if ((turno.NumeroTurnos >= int(cant.split('-')[0])) and (turno.NumeroTurnos <= int(cant.split('-')[1]))):
                        pass
                    else:
                        return False
            elif (req == 'Egresos'):
                if(cant[0] == '>'):
                    if(turno.Egresos > int(cant.split('>')[1])):
                        pass
                    else:
                        return False
                elif(cant[0] == '<'):
                    if(turno.Egresos < int(cant.split('<')[1])):
                        pass
                    else:
                        return False
                elif(cant[0] == '='):
                    if(turno.Egresos < int(cant.split('=')[1])):
                        pass
                    else:
                        return False
                elif(cant.find('-') > 0):
                    if ((turno.Egresos >= int(cant.split('-')[0])) and (turno.Egresos <= int(cant.split('-')[1]))):
                        pass
                    else:
                        return False
        return True

def getSeleccion(queryset, tipoEvento, eventos, turno):
    df = pd.DataFrame(list(queryset.values()))
    df['FrecuenciaAcumulada'] = df['Frecuencia'].cumsum()
    limite_inferior = df['FrecuenciaAcumulada'].min()
    limite_superior = df['FrecuenciaAcumulada'].max()
    seleccion = random.uniform(limite_inferior,limite_superior)
    df = df.sample(frac=1).reset_index(drop=True)
    for index, row in df.iterrows():
        if ((row['FrecuenciaAcumulada'] >= seleccion) and (verificarRequisitos(row['Evento_id'], turno,'Evento'))):
                desc = Evento.objects.get(id=row['Evento_id'])
                desc = str(desc.Descripcion)
                temp = row[['Evento_id']].to_dict()
                temp['Descripcion'] = desc
                if(tipoEvento == 'Micro'):
                        temp['TipoEvento'] = 'Micro'
                        eventos.append(temp)
                        break
                else:
                    temp['TipoEvento'] = 'Macro'
                    eventos.append(temp)
                    break
        else:
            pass



def seleccionEvento(user):
    turno = Turnos.objects.filter(User=user).first()
    eventos = []
    seleccion = 0
    eventosDisp = Evento_User.objects.values_list('Evento','Frecuencia','TipoEvento').exclude(Frecuencia=0)
    micro_id = TipoEvento.objects.get(TipoEvento = 'Micro').pk
    query_micro = eventosDisp.filter(TipoEvento=micro_id, User=user)
    if not query_micro:
        return eventos.append({})
    getSeleccion(query_micro, 'Micro', eventos, turno)
    seleccion = random.uniform(0,1)
    if(seleccion >= .7):
        macro_id = TipoEvento.objects.get(TipoEvento = 'Macro').pk
        query_macro = eventosDisp.filter(TipoEvento=macro_id, User=user)
        getSeleccion(query_macro, 'Macro', eventos, turno)
    else:
        eventos.append({})
    return eventos

###################################################################

###################################################################
"""
PREGUNTA
"""

def modifyPregunta(user, pregunta):
    preguntaUser = Preguntas_User.objects.get(User=user.id, Pregunta=pregunta.id)
    Preguntas_User.objects.filter(User=user.id, Pregunta=pregunta.id).update(Frecuencia=preguntaUser.Frecuencia - 1)

def preguntaAfecta(user, pregunta):
    afectaList = []
    afecta_pregunta = Preguntas_Afecta.objects.filter(Preguntas=pregunta)
    tipoInversion = TipoPregunta.objects.filter(id=pregunta.TipoPreguntas.id).first()
    for afecta in afecta_pregunta:
        duracion = Periodo.objects.filter(TipoPeriodo=afecta.Periodo).first()
        if tipoInversion.SaldoInversion != 'GananciaCapital':
            tipoAfecta = afectaInversion(afecta, user)
            if tipoAfecta:
                afecta_usuario = Afecta_user(User=user, Descripcion=pregunta.Descripcion, Afecta=afecta.Afecta, TurnosEsperar=duracion.Turnos, TurnosRestante=duracion.Turnos, Cantidad=afecta.Cantidad, Duracion=afecta.Duracion)
                afecta_usuario.save()
                afectaList.append(afecta_usuario.id)
        else:
            if str(afecta.Afecta) == 'DineroEfectivo' and afecta.Periodo.Turnos != -1:
                rangoRendimiento = (tipoInversion.TasaRendimiento).split(" ")
                limite_inferior = float(rangoRendimiento[0])
                limite_superior = float(rangoRendimiento[2])
                tasaRendimiento = random.uniform(limite_inferior,limite_superior)
                cantidad = (Decimal(afecta.Cantidad) * -1)
                inversionPregunta = InversionPregunta(User=user, Descripcion=pregunta.Descripcion, TipoInversion=tipoInversion, SaldoInicial=cantidad, InicialMasAportacion=cantidad, EventoExterno=0, TazaRendimiento=tasaRendimiento, Aportacion=0, SaldoActual=cantidad, SaldoInvercion= tipoInversion.SaldoInversion)
                inversionPregunta.save()
            tipoAfecta = afectaInversion(afecta, user)
            if tipoAfecta:
                afecta_usuario = Afecta_user(User=user, Descripcion=pregunta.Descripcion, Afecta=afecta.Afecta, TurnosEsperar=duracion.Turnos, TurnosRestante=duracion.Turnos, Cantidad=afecta.Cantidad, Duracion=afecta.Duracion)
                afecta_usuario.save()
                afectaList.append(afecta_usuario.id)
    return afectaList

def validarPregunta(user, pregunta):
    turno = Turnos.objects.filter(User=user).first()
    afecta_pregunta = Preguntas_Afecta.objects.filter(Preguntas=pregunta)
    for afecta in afecta_pregunta:
        duracion = Periodo.objects.filter(TipoPeriodo=afecta.Periodo).first()
        if duracion.Turnos == -1:
            if str(afecta.Afecta) == 'DineroEfectivo':
                if turno.DineroEfectivo < Decimal(afecta.Cantidad):
                    return False
            if str(afecta.Afecta) == 'Felicidad':
                if turno.Felicidad < afecta.Felicidad:
                    return False
            if str(afecta.Afecta) == 'Egresos':
                if turno.Egresos < afecta.Egresos:
                    return False
            if str(afecta.Afecta) == 'Ingresos':
                if turno.Ingresos < afecta.Ingresos:
                    return False
    return True
            
def getAfectaPregunta(response):
    for i in response:
        if i != {}:
            i['Afecta'] = []
            pregunta = Preguntas.objects.filter(id = i["Pregunta_id"]).first()
            afectas = Preguntas_Afecta.objects.filter(Preguntas = pregunta)
            for afecta in afectas:
                if afecta.Periodo.Turnos != -1:
                    periodo = str(afecta.Periodo)
                    if afecta.Periodo.Turnos < 0:
                        periodo = "Exclusivo"
                    duracion = afecta.Duracion
                    if afecta.Duracion > 1000:
                        duracion = "Infinito"
                    i['Afecta'].append({"Afecta": afecta.Afecta.TipoAfect, "Cantidad": afecta.Cantidad, "Periodo":periodo, "Duracion":duracion})

def afectaInversion(afecta, user):
    listaInversionAfecta = ['Telecomunicaciones', 'Tecnologia', 'Construccion', 'Bienes_Raices']
    if str(afecta.Afecta) in listaInversionAfecta:
        inversionesAcciones = Inversion.objects.filter(TipoEmpresa=afecta.Afecta, User=user)
        for inversion in inversionesAcciones:
            inversion.EventoExterno = afecta.Cantidad
            inversion.save()
        #Checar como funciona el Evento externo en inversinPregunta
        return False
    else:
        if str(afecta.Afecta) == "GananciaCapital":
            inversionesPregunta = InversionPregunta.objects.filter(User=user)
            if int(len(inversionesPregunta)) > 0:
                seleccion = random.randint(int(1),int(len(inversionesPregunta))) -1
            else: seleccion = 1
            cont = 1
            for inversion in inversionesPregunta:
                if cont == seleccion:
                    inversion.EventoExterno = afecta.Cantidad
                    inversion.save()
                cont = cont + 1

        return True

def getSeleccionPregunta(queryset, tipoEvento, preguntas, turno):
    df = pd.DataFrame(list(queryset.values()))
    df['FrecuenciaAcumulada'] = df['Frecuencia'].cumsum()
    df = df.sample(frac=1).reset_index(drop=True)
    for x in range(0,4,1):
        limite_inferior = df['FrecuenciaAcumulada'].min()
        limite_superior = df['FrecuenciaAcumulada'].max()
        borrar = -10
        seleccion = random.uniform(limite_inferior,limite_superior)
        for index, row in df.iterrows():
            if ((row['FrecuenciaAcumulada'] >= seleccion) and (verificarRequisitos(row['Pregunta_id'], turno, 'Pregunta'))):
                desc = Preguntas.objects.get(id=row['Pregunta_id'])
                desc = str(desc.Descripcion)
                descTipo = TipoPregunta.objects.get(id=row['TipoPreguntas_id'])
                descTipo = str(descTipo.TipoPregunta).split('_')[0]
                temp = row[['Pregunta_id']].to_dict()
                temp['Descripcion'] = desc
                temp['TipoPregunta'] = descTipo
                preguntas.append(temp)
                borrar = index
                df.drop(borrar, inplace = True, errors = 'ignore' )
                borrar = -10
                break
            else:
                pass

        

def seleccionPregunta(user):
    turno = Turnos.objects.filter(User=user).first()
    preguntas = []
    PreguntasDisp = Preguntas_User.objects.values_list('Pregunta','Frecuencia','TipoPreguntas').exclude(Frecuencia=0)
    inversion_id = TipoPregunta.objects.values_list('id',flat=True).filter(TipoPregunta__startswith = 'Inversion')
    diversion_id = TipoPregunta.objects.get(TipoPregunta = 'Diversion').pk
    bienes_id = TipoPregunta.objects.get(TipoPregunta = 'Bienes Personales').pk
    laboral_id = TipoPregunta.objects.get(TipoPregunta= 'Laboral').pk
    query_inversion = PreguntasDisp.filter(TipoPreguntas__in=inversion_id, User=user)
    query_diversion = PreguntasDisp.filter(TipoPreguntas=diversion_id,User=user)
    query_bienes = PreguntasDisp.filter(TipoPreguntas=bienes_id,User=user)
    query_laboral = PreguntasDisp.filter(TipoPreguntas=laboral_id,User=user)
    getSeleccionPregunta(query_inversion, 'Inversion', preguntas, turno)
    getSeleccionPregunta(query_diversion, 'Diversion', preguntas, turno)
    getSeleccionPregunta(query_bienes, 'Bienes Personales', preguntas, turno)
    getSeleccionPregunta(query_laboral, 'Laboral', preguntas, turno)
    return preguntas 

###################################################################

###################################################################
"""
INICIO DE TURNO
"""
def afectaTurnoinstantaneo(afectaActions, turno):
    for afecta in afectaActions:
        afecta.TurnosRestante = afecta.TurnosRestante - 1
        afecta.save()
        if afecta.TurnosRestante <= 0:
            afecta.Duracion = afecta.Duracion - 1
            afecta.save()
            if afecta.TurnosEsperar <= 0:
                afecta.delete()
            else:
                if afecta.Cantidad[0] == '%':
                    cantidadAfecta = afecta.Cantidad[1:]
                    if cantidadAfecta[0] == '-':
                        cantidadAfecta = cantidadAfecta[1:]
                        modifyTurno(turno, afecta.Afecta, cantidadAfecta, True, False)
                    else:
                        modifyTurno(turno, afecta.Afecta, cantidadAfecta, True, True)
                else:
                    modifyTurno(turno, afecta.Afecta, afecta.Cantidad, False, True)
                afecta.TurnosRestante = afecta.TurnosEsperar
                afecta.save()
                turno.save()
                if afecta.Duracion <= 0: 
                    afecta.delete()

#Se aplican todos los afectas relacionados con el usuario
def afectaTurnos(user, turno):
    
    afectaActions = Afecta_user.objects.filter(User=user)
    for afecta in afectaActions:
        afecta.TurnosRestante = afecta.TurnosRestante - 1
        afecta.save()
        if afecta.TurnosRestante <= 0:
            afecta.Duracion = afecta.Duracion - 1
            afecta.save()
            if afecta.TurnosEsperar <= 0:
                afecta.delete()
            else:
                if afecta.Cantidad[0] == '%':
                    cantidadAfecta = afecta.Cantidad[1:]
                    if cantidadAfecta[0] == '-':
                        cantidadAfecta = cantidadAfecta[1:]
                        modifyTurno(turno, afecta.Afecta, cantidadAfecta, True, False)
                    else:
                        modifyTurno(turno, afecta.Afecta, cantidadAfecta, True, True)
                else:
                    modifyTurno(turno, afecta.Afecta, afecta.Cantidad, False, True)
                afecta.TurnosRestante = afecta.TurnosEsperar
                afecta.save()
                turno.save()
                if afecta.Duracion <= 0: 
                    afecta.delete()
                
#Es la forma en la que se modifica el turno actual del usuario (Se puede cambiar)   
def modifyTurno(turno, afecta, cantidad, porcentaje, suma):
    if afecta == 'Felicidad':
        if porcentaje:
            if suma:
                turno.Felicidad = turno.Felicidad + (turno.Felicidad * Decimal(float(cantidad)/100))
                turno.save()
                return True
            turno.Felicidad = turno.Felicidad - (turno.Felicidad * Decimal(float(cantidad)/100))
            turno.save()
            return True
        turno.Felicidad = turno.Felicidad + Decimal(cantidad)
        turno.save()
        return True

    elif afecta == 'DineroEfectivo':
        if porcentaje:
            if suma:
                turno.DineroEfectivo = turno.DineroEfectivo + (turno.DineroEfectivo * Decimal(float(cantidad)/100))
                return True
            turno.DineroEfectivo = turno.DineroEfectivo - (turno.DineroEfectivo * Decimal(float(cantidad)/100))
            return True
        turno.DineroEfectivo = turno.DineroEfectivo + Decimal(cantidad)
        return True
    elif afecta == 'Sueldo':
        sueldoActual = Afecta_user.objects.filter(User=turno.User, Afecta='SueldoReal').first()
        if porcentaje:
            if suma:
                sueldoActual.Cantidad = str(Decimal(sueldoActual.Cantidad) + (Decimal(sueldoActual.Cantidad) * Decimal(float(cantidad)/100)))
                sueldoActual.save()
                return True
            sueldoActual.Cantidad = str(Decimal(sueldoActual.Cantidad) - (Decimal(sueldoActual.Cantidad) * Decimal(float(cantidad)/100)))
            sueldoActual.save()
            return True
        sueldoActual.Cantidad = str(Decimal(sueldoActual.Cantidad) + Decimal(cantidad))
        sueldoActual.save()
        return True
    elif afecta == 'SueldoReal':
        if porcentaje:
            if suma:
                turno.DineroEfectivo = turno.DineroEfectivo + (turno.DineroEfectivo * Decimal(float(cantidad)/100))
                return True
            turno.DineroEfectivo = turno.DineroEfectivo - (turno.DineroEfectivo * Decimal(float(cantidad)/100))
            return True
        turno.DineroEfectivo = turno.DineroEfectivo + Decimal(cantidad)
    ######################
    elif afecta == 'EgresoPersonal':
        if porcentaje:
            if suma:
                turno.DineroEfectivo = turno.DineroEfectivo + (turno.DineroEfectivo * Decimal(float(cantidad)/100))
                return True
            turno.DineroEfectivo = turno.DineroEfectivo - (turno.DineroEfectivo * Decimal(float(cantidad)/100))
            return True
        turno.DineroEfectivo = turno.DineroEfectivo + Decimal(cantidad)
    #####################
    elif 'Inversion' in str(afecta):
        turno.DineroEfectivo = turno.DineroEfectivo + Decimal(cantidad)
    elif afecta == 'Ingresos':
        turno.DineroEfectivo = turno.DineroEfectivo + Decimal(cantidad)
    elif afecta == 'Egresos':
        turno.DineroEfectivo = turno.DineroEfectivo - Decimal(cantidad)

def turnoIngresosEgresos(user, turno):
   
    prestamos = Prestamo.objects.filter(User = user)
    inversiones = Inversion.objects.filter(User = user)
    ingresos = Afecta_user.objects.filter(Afecta = 'Ingresos', User = user)
    egresos = Afecta_user.objects.filter(Afecta = 'Egresos', User = user)
    inversionesAfecta = Afecta_user.objects.filter(Afecta__startswith = 'Inversion', User = user)
    inversionPregunta = InversionPregunta.objects.filter(User = user)
    sueldoActual = Afecta_user.objects.filter(User=user, Afecta='SueldoReal').first()
  
    turnoEgresos = Decimal(8000)
    turnoIngresos = Decimal(sueldoActual.Cantidad)

    for prestamo in prestamos:
        turnoEgresos = turnoEgresos + Decimal(prestamo.Mensualidad)

  
    #No es un ingreso por que no lo recibes mensualmente
    """
    for inversion in inversiones:
        turnoIngresos = turnoIngresos + inversion.SaldoActual
    """

    for ingreso in ingresos:
        portafolioCantidad = afectaMensual(ingreso)
        turnoIngresos = turnoIngresos + portafolioCantidad

    for egreso in egresos:
        portafolioCantidad = afectaMensual(egreso)
        turnoEgresos = turnoEgresos + Decimal(portafolioCantidad)

    for inversion in inversionesAfecta:
        portafolioCantidad = afectaMensual(inversion)
        turnoIngresos = turnoIngresos + portafolioCantidad

    #No es un ingreso por que no lo recibes mensualmente
    """
    for inversion in inversionPregunta:
        turnoIngresos = turnoIngresos + inversion.SaldoActual
    """
 
    turno.Ingresos = turnoIngresos
    turno.Egresos = turnoEgresos
    turno.save()

def afectaMensual(afecta):
    if afecta.TurnosEsperar > 4:
        numDividir = afecta.TurnosEsperar / 4
        afectaCantidad = Decimal(afecta.Cantidad) / Decimal(numDividir)
    elif afecta.TurnosEsperar == 2:
        afectaCantidad = Decimal(afecta.Cantidad) * 2
    elif afecta.TurnosEsperar == 1:
        afectaCantidad = Decimal(afecta.Cantidad) * 4
    else :
        afectaCantidad = Decimal(afecta.Cantidad)
    return Decimal(afectaCantidad)


def prestamosTurnos(user, turno, prestamos):

    for prestamo in prestamos:
        if prestamo.Frecuencia <= 0:
            turno.DineroEfectivo = turno.DineroEfectivo - prestamo.Mensualidad
            tipoPrestamo = prestamo.idPrestamo
            tipoPrestamo = TipoPrestamo.objects.filter(idPrestamo = str(tipoPrestamo)).first()

            interes = re.sub('%', '',str(tipoPrestamo.TazaInteres) )
            interes = float(interes)/100
            interesMensual = prestamo.SaldoAbsoluto * Decimal(interes/12)

            prestamo.SaldoAbsoluto = prestamo.SaldoAbsoluto - (prestamo.Mensualidad - interesMensual)

            if prestamo.SaldoAbsoluto < prestamo.Mensualidad:
                prestamo.Mensualidad = prestamo.SaldoAbsoluto

            interes = re.sub('%', '',str(tipoPrestamo.TazaInteres) )
            interes = float(interes)/100
            interesMensual = prestamo.SaldoAbsoluto * Decimal(interes/12)

            prestamo.Frecuencia = 3
            prestamo.Interes = interesMensual
            prestamo.save()

            if prestamo.SaldoAbsoluto <= 0:
                prestamo.delete()
            turno.save()
        else:
            prestamo.Frecuencia = prestamo.Frecuencia - 1
            prestamo.save()

        

def inversionesTurnos(user, turno, inversiones):

    for inversion in inversiones:
        compania = TipoInversiones.objects.filter(id=inversion.TipoInversion.id).first()

        rangoRendimiento = (compania.RangoRendimiento).split(" ")
        limite_inferior = float(rangoRendimiento[0])
        limite_superior = float(rangoRendimiento[2])
        tasaRendimiento = random.uniform(limite_inferior,limite_superior)

        if float(inversion.EventoExterno) != 0:
            inversion.SaldoActual = inversion.SaldoActual + (inversion.SaldoActual * Decimal(inversion.EventoExterno))
            inversion.EventoExterno == 0
            inversion.save()

        inversion.TasaRendimiento = tasaRendimiento
        inversion.SaldoActual = inversion.SaldoActual + (inversion.SaldoActual * Decimal(inversion.TasaRendimiento))
        inversion.save()

def inversionesPreguntasTurnos(user, turno, inversionesPregunta):
    for inversion in inversionesPregunta:
        tipoInversion = TipoPregunta.objects.filter(id=inversion.TipoInversion.id).first()

        rangoRendimiento = (tipoInversion.TasaRendimiento).split(" ")
        limite_inferior = float(rangoRendimiento[0])
        limite_superior = float(rangoRendimiento[2])
        tasaRendimiento = random.uniform(limite_inferior,limite_superior)

        if float(inversion.EventoExterno) != 0:
            inversion.SaldoActual = inversion.SaldoActual + (inversion.SaldoActual * Decimal(inversion.EventoExterno))
            inversion.EventoExterno == 0
            inversion.save()

        ###### ver el video del profe para entender bien como funciona ######
        inversion.TazaRendimiento = tasaRendimiento
        inversion.SaldoActual = inversion.SaldoActual + (inversion.SaldoActual * Decimal(inversion.TazaRendimiento))
        inversion.save()

###################################################################

###################################################################

def riesgoInversion(rangoRendimiento):
    rango = rangoRendimiento.split(" ")
    limBajo = float(rango[0])
    limAlto = float(rango[2])

    if limBajo < 0 and limAlto <= 0:
        return "Muy Bajo"
    elif limBajo < 0 and limAlto + limBajo <= 0 and limAlto - limBajo > 1:
        return "Muy Bajo"
    elif limBajo < 0 and limAlto + limBajo <= 0 and limAlto - limBajo > .5:
        return "Bajo"
    elif limBajo < 0:
        return "Medio"
    elif limAlto - limBajo < .2:
        return "Alto"
    return "Muy Alto"


###################################################################

###################################################################

def borrarInfoUser(user):
    prestamos = Prestamo.objects.filter(User=user)
    afecta = Afecta_user.objects.filter(User=user)
    turno = Turnos.objects.filter(User=user)
    inversiones = Inversion.objects.filter(User = user)
    inversionPregunta = InversionPregunta.objects.filter(User = user)
    preguntas = Preguntas_User.objects.filter(User = user)
    eventos = Evento_User.objects.filter(User = user)


    eventos.delete()
    preguntas.delete()
    inversionPregunta.delete()
    inversiones.delete()
    turno.delete()
    afecta.delete()
    prestamos.delete()

def reiniciarUser(user):

    #Crear turno actual del usuario
    newTurno = Turnos(NumeroTurnos=0, Felicidad=50, DineroEfectivo=20000, Ingresos=1000, Egresos=0, Sueldo=15000, User=user)
    newTurno.save()

    #Crear relacion con todos los eventos
    eventos = Evento.objects.all()
    for event in eventos:
        user_event = Evento_User(User=user, Evento=event, Frecuencia=event.Frecuencia, TipoEvento=event.TipoEvento)
        user_event.save()

    #Crear relacion con todas las preguntas
    preguntas = Preguntas.objects.all()
    for pregu in preguntas:
        user_pregu = Preguntas_User(User=user, Pregunta=pregu, Frecuencia=pregu.Frecuencia, TipoPreguntas=pregu.TipoPreguntas)
        user_pregu.save()
    
    #Crear afecta de sueldo
    user_afecta = Afecta_user(Afecta="SueldoReal", Descripcion="Eres empleado", User=user, TurnosEsperar=4, TurnosRestante=4, Cantidad=newTurno.Sueldo, Duracion=99999999)
    user_afecta.save()